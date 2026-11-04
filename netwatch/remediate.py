"""Automated remediation: withdraw suspect links from the routing view,
reconverge, and verify with fresh probes."""
from .spf import build_fibs
from .monitor import probe_all, summarize


def remediate(topo, ranked, max_actions=3):
    """Withdraw top suspects one at a time until probes are all healthy.
    Returns (withdrawn_links, fibs, results, healthy)."""
    # Start from the control plane's current (stale) belief: it still thinks every link is up.
    believed = set(topo.cost)
    withdrawn = []
    fibs = build_fibs(topo, believed)
    results = probe_all(topo, fibs)
    if not ranked and summarize(results)["failed"] == 0:
        return withdrawn, fibs, results, True
    for link, _, _ in ranked[:max_actions]:
        believed = believed - {link}
        withdrawn.append(link)
        fibs = build_fibs(topo, believed)
        results = probe_all(topo, fibs)
        if summarize(results)["failed"] == 0:
            return withdrawn, fibs, results, True
    return withdrawn, fibs, results, False
