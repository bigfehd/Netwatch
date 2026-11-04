"""CLI:  python -m netwatch demo | bench"""
import random
import sys
import time

from .topology import random_topology
from .spf import build_fibs
from .monitor import probe_all, summarize, metrics_text
from .rca import diagnose
from .remediate import remediate


def _connected_without(topo, link):
    """Would the network stay connected if `link` failed?"""
    seen, stack = set(), [next(iter(topo.nodes))]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        for v in topo.adj[u]:
            k = (u, v) if u <= v else (v, u)
            if k != link and topo.up[k]:
                stack.append(v)
    return len(seen) == len(topo.nodes)


def run_incident(topo, baseline_fibs, baseline_results, failed_links):
    """Fail links (control plane does not know yet), detect, diagnose, remediate."""
    for a, b in failed_links:
        topo.set_state(a, b, False)
    results = probe_all(topo, baseline_fibs)       # stale FIBs: traffic blackholes
    s = summarize(results)
    ranked = diagnose(baseline_results, s["failed_pairs"])
    withdrawn, _, after, healthy = remediate(topo, ranked, max_actions=len(failed_links) + 2)
    for a, b in failed_links:                      # restore for the next trial
        topo.set_state(a, b, True)
    return s, ranked, withdrawn, healthy


def demo():
    topo = random_topology(12, 8, seed=7)
    fibs = build_fibs(topo, set(topo.cost))
    base = probe_all(topo, fibs)
    print(f"Topology: {len(topo.nodes)} routers, {len(topo.cost)} links")
    print("Healthy:", summarize(base)["failed"], "failed probes of", len(base))
    from .rca import baseline_link_usage
    usage = baseline_link_usage(base)
    link = max(usage, key=lambda k: (len(usage[k]), k))   # a heavily used link
    print(f"\nInjecting failure on link {link[0]} <-> {link[1]} (control plane unaware)")
    topo.set_state(*link, False)
    broken = probe_all(topo, fibs)
    s = summarize(broken)
    print(f"Detected: {s['failed']} of {s['total']} probes failing")
    print(metrics_text(broken))
    ranked = diagnose(base, s["failed_pairs"])
    print("RCA ranking (link, score, failing pairs explained):")
    for l, sc, hit in ranked[:3]:
        print(f"  {l[0]} <-> {l[1]}  score={sc:.2f}  explains={hit}")
    withdrawn, _, after, healthy = remediate(topo, ranked)
    print(f"\nRemediation withdrew: {withdrawn}")
    print(f"Verified after reconvergence: {summarize(after)['failed']} failing probes -> healthy={healthy}")


def bench(n=60, extra=60, trials=200, seed=1):
    rng = random.Random(seed)
    topo = random_topology(n, extra, seed=seed)
    t0 = time.perf_counter()
    fibs = build_fibs(topo, set(topo.cost))
    spf_ms = (time.perf_counter() - t0) * 1000
    base = probe_all(topo, fibs)
    safe = [l for l in topo.links() if _connected_without(topo, l)]
    top1 = top3 = fixed = detected = 0
    ran = 0
    for _ in range(trials):
        link = rng.choice(safe)
        s, ranked, withdrawn, healthy = run_incident(topo, fibs, base, [link])
        if s["failed"] == 0:
            continue                               # failed link carried no best paths
        ran += 1
        detected += 1
        order = [r[0] for r in ranked]
        top1 += order[0] == link
        top3 += link in order[:3]
        fixed += healthy
    print(f"nodes={n} links={len(topo.cost)} probes/round={len(base)}")
    print(f"full SPF + FIB build for all routers: {spf_ms:.1f} ms")
    print(f"single-link failure trials with detected impact: {ran}")
    print(f"RCA top-1 correct: {top1}/{ran} ({100*top1/ran:.1f}%)")
    print(f"RCA top-3 correct: {top3}/{ran} ({100*top3/ran:.1f}%)")
    print(f"remediation restored full reachability: {fixed}/{ran} ({100*fixed/ran:.1f}%)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    {"demo": demo, "bench": bench}[cmd]()
