from common.metrics import run_timed, summarize_latencies


def run(platform, start_ids, iterations, warmup):
    idx = {"i": 0}

    def point():
        sid = start_ids[idx["i"] % len(start_ids)]
        idx["i"] += 1
        platform.point_lookup(sid)

    point_latencies = run_timed(point, iterations=iterations, warmup=warmup)

    idx2 = {"i": 0}

    def filtered():
        sid = start_ids[idx2["i"] % len(start_ids)]
        idx2["i"] += 1
        platform.filtered_lookup(sid)

    filtered_latencies = run_timed(filtered, iterations=iterations, warmup=warmup)

    return {
        "point_lookup": summarize_latencies(point_latencies),
        "filtered_lookup": summarize_latencies(filtered_latencies),
    }
