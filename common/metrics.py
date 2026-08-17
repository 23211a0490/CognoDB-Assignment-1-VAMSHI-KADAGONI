"""Timing and percentile helpers shared by every workload."""
import time
import statistics
from contextlib import contextmanager


@contextmanager
def timer():
    """Usage: with timer() as t: ...; t.elapsed_ms"""
    start = time.perf_counter()
    result = _TimerResult()
    yield result
    result.elapsed_ms = (time.perf_counter() - start) * 1000


class _TimerResult:
    elapsed_ms: float = 0.0


def percentiles(latencies_ms, pcts=(50, 95)):
    """latencies_ms: list of floats. Returns dict like {'p50': .., 'p95': ..}."""
    if not latencies_ms:
        return {f"p{p}": None for p in pcts}
    sorted_lat = sorted(latencies_ms)
    out = {}
    for p in pcts:
        # nearest-rank method
        idx = max(0, min(len(sorted_lat) - 1, int(round(p / 100 * (len(sorted_lat) - 1)))))
        out[f"p{p}"] = round(sorted_lat[idx], 3)
    return out


def run_timed(fn, iterations: int, warmup: int = 0):
    """
    Runs fn() `warmup` times (discarded), then `iterations` times, timing each
    call individually. Returns list of per-call latencies in ms.
    """
    for _ in range(warmup):
        fn()
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        latencies.append((time.perf_counter() - start) * 1000)
    return latencies


def summarize_latencies(latencies_ms):
    if not latencies_ms:
        return {"p50": None, "p95": None, "mean": None, "n": 0}
    p = percentiles(latencies_ms)
    return {
        "p50": p["p50"],
        "p95": p["p95"],
        "mean": round(statistics.mean(latencies_ms), 3),
        "n": len(latencies_ms),
    }
