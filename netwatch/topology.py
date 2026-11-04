"""Network topology: routers, weighted bidirectional links, up/down state."""
import random


def _key(a, b):
    return (a, b) if a <= b else (b, a)


class Topology:
    def __init__(self):
        self.nodes = set()
        self.cost = {}   # link key -> OSPF-style cost
        self.up = {}     # link key -> actual physical state
        self.adj = {}    # node -> set of neighbours

    def add_link(self, a, b, cost=1):
        k = _key(a, b)
        self.nodes.update((a, b))
        self.cost[k] = cost
        self.up[k] = True
        self.adj.setdefault(a, set()).add(b)
        self.adj.setdefault(b, set()).add(a)

    def links(self):
        return list(self.cost)

    def is_up(self, a, b):
        return self.up.get(_key(a, b), False)

    def set_state(self, a, b, up):
        self.up[_key(a, b)] = up

    def link_cost(self, a, b):
        return self.cost[_key(a, b)]

    def believed_up(self):
        """The set of links the control plane currently believes are up."""
        return {k for k, v in self.up.items() if v}


def random_topology(n, extra_links, seed=0):
    """Connected random topology: a ring plus random chords, random costs."""
    rng = random.Random(seed)
    t = Topology()
    names = [f"r{i}" for i in range(n)]
    for i in range(n):
        t.add_link(names[i], names[(i + 1) % n], rng.randint(1, 10))
    added = 0
    while added < extra_links:
        a, b = rng.sample(names, 2)
        if _key(a, b) not in t.cost:
            t.add_link(a, b, rng.randint(1, 10))
            added += 1
    return t
