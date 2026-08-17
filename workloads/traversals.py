from common.metrics import run_timed, summarize_latencies


def run(platform, start_ids, iterations, warmup):
    """
    For each hop depth (1, 2, 3), runs `iterations` traversals (after warmup)
    cycling through the same `start_ids` list for every platform, so every
    platform is tested against identical start points.
    """
    results = {}
    for hops in (1, 2, 3):
        idx = {"i": 0}

        def call():
            sid = start_ids[idx["i"] % len(start_ids)]
            idx["i"] += 1
            platform.traverse(sid, hops)

        latencies = run_timed(call, iterations=iterations, warmup=warmup)
        results[f"{hops}_hop"] = summarize_latencies(latencies)
    return results
