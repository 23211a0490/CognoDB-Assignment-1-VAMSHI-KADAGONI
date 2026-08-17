"""
Concurrent read/write throughput. Each client thread runs its own loop of
mostly-reads / some-writes for `duration_seconds`, and we sum completed ops
across all threads to get sustained queries/sec at that concurrency level.

Note: this spins up one platform connection per thread (most drivers,
including the neo4j driver, are not meant to share a session across threads).
`platform_factory()` must return a *new*, already-connected instance.
"""
import random
import threading
import time


def _client_loop(platform_factory, node_ids, duration_seconds, read_write_ratio, counter, lock):
    p = platform_factory()
    p.connect()

    rng = random.Random()
    end_at = time.perf_counter() + duration_seconds
    local_count = 0

    try:
        while time.perf_counter() < end_at:
            nid = rng.choice(node_ids)

            try:
                if rng.random() < read_write_ratio:
                    p.mixed_read(nid)
                else:
                    # Retry writes if a transaction conflict occurs
                    for attempt in range(3):
                        try:
                            p.mixed_write(nid)
                            break
                        except Exception:
                            if attempt == 2:
                                raise
                            time.sleep(0.05 * (attempt + 1))

                local_count += 1

            except Exception as e:
                # Skip this operation and continue the benchmark
                print(f"Operation skipped: {e}")

    finally:
        p.close()

    with lock:
        counter["ops"] += local_count


def run(platform_factory, node_ids, concurrency_levels, duration_seconds, read_write_ratio=0.8):
    """
    platform_factory: zero-arg callable returning a fresh, unconnected
        platform instance (e.g. lambda: CognoDBPlatform()).
    Returns {"10_clients": {"qps": .., "total_ops": .., "duration_seconds": ..}, ...}
    """
    results = {}
    for n in concurrency_levels:
        counter = {"ops": 0}
        lock = threading.Lock()
        threads = [
            threading.Thread(
                target=_client_loop,
                args=(platform_factory, node_ids, duration_seconds, read_write_ratio, counter, lock),
            )
            for _ in range(n)
        ]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start
        results[f"{n}_clients"] = {
            "qps": round(counter["ops"] / elapsed, 2) if elapsed else 0,
            "total_ops": counter["ops"],
            "duration_seconds": round(elapsed, 2),
        }
    return results
