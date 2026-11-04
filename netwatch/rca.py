"""Root-cause analysis: correlate failed probe paths with healthy-state paths
to rank which links most likely explain the failures (network tomography)."""


def _links_on(path):
    return [(a, b) if a <= b else (b, a) for a, b in zip(path, path[1:])]


def baseline_link_usage(baseline_results):
    """For each link, the set of probe pairs whose healthy-state path crosses it."""
    usage = {}
    for pair, (_, path) in baseline_results.items():
        for k in _links_on(path):
            usage.setdefault(k, set()).add(pair)
    return usage


def diagnose(baseline_results, failed_pairs):
    """Rank links. Score = fraction of baseline paths through the link that now
    fail; ties broken by how many failing pairs the link explains."""
    usage = baseline_link_usage(baseline_results)
    failed = set(failed_pairs)
    ranked = []
    for link, pairs in usage.items():
        hit = len(pairs & failed)
        if hit:
            ranked.append((link, hit / len(pairs), hit))
    ranked.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return ranked
