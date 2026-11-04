"""Data-plane probing: forward packets hop by hop using each router's FIB
against the *actual* link state, and classify the outcome."""

OK, BLACKHOLE, LOOP, NOROUTE = "ok", "blackhole", "loop", "noroute"


def trace(topo, fibs, src, dst, ttl=64):
    path = [src]
    cur = src
    for _ in range(ttl):
        if cur == dst:
            return OK, path
        nh = fibs[cur].get(dst)
        if nh is None:
            return NOROUTE, path
        if not topo.is_up(cur, nh):
            return BLACKHOLE, path
        path.append(nh)
        cur = nh
    return LOOP, path


def probe_all(topo, fibs):
    """Probe every ordered router pair. Returns {(src, dst): (status, path)}."""
    return {(s, d): trace(topo, fibs, s, d)
            for s in topo.nodes for d in topo.nodes if s != d}


def summarize(results):
    failed = [p for p, (st, _) in results.items() if st != OK]
    return {"total": len(results), "failed": len(failed), "failed_pairs": failed}


def metrics_text(results):
    """Prometheus text exposition format."""
    s = summarize(results)
    by = {}
    for _, (st, _) in results.items():
        by[st] = by.get(st, 0) + 1
    lines = [
        "# HELP netwatch_probes_total Probes sent between all router pairs.",
        "# TYPE netwatch_probes_total gauge",
        f"netwatch_probes_total {s['total']}",
        "# HELP netwatch_probe_results Probe outcomes by status.",
        "# TYPE netwatch_probe_results gauge",
    ]
    for st in (OK, BLACKHOLE, LOOP, NOROUTE):
        lines.append(f'netwatch_probe_results{{status="{st}"}} {by.get(st, 0)}')
    lines.append(f"netwatch_reachability_ratio {1 - s['failed'] / s['total']:.6f}")
    return "\n".join(lines) + "\n"
