from common.metrics import run_timed, summarize_latencies


def run(platform, iterations, warmup):
    latencies = run_timed(
        platform.aggregate_count_by_type, iterations=iterations, warmup=warmup
    )
    return {"count_by_rel_type": summarize_latencies(latencies)}
