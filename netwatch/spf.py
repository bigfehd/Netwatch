"""Link-state routing: Dijkstra SPF and FIB construction (OSPF-style)."""
import heapq


def spf(topo, src, believed):
    """Shortest paths from src over the links in `believed`.
    Returns {dst: first_hop}. Ties are broken deterministically by name."""
    dist = {src: 0}
    first = {src: None}
    heap = [(0, src, None)]
    done = set()
    while heap:
        d, u, fh = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        for v in sorted(topo.adj.get(u, ())):
            k = (u, v) if u <= v else (v, u)
            if k not in believed:
                continue
            nd = d + topo.cost[k]
            nfh = v if u == src else first[u]
            if v not in dist or nd < dist[v] or (nd == dist[v] and v not in done and nfh < first[v]):
                dist[v] = nd
                first[v] = nfh
                heapq.heappush(heap, (nd, v, nfh))
    return {d: fh for d, fh in first.items() if d != src}


def build_fibs(topo, believed):
    """Every router computes its own forwarding table from the shared link-state view."""
    return {n: spf(topo, n, believed) for n in topo.nodes}
