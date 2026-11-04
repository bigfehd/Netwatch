import unittest

from netwatch.topology import Topology, random_topology
from netwatch.spf import spf, build_fibs
from netwatch.monitor import probe_all, summarize, trace, OK, BLACKHOLE, LOOP
from netwatch.rca import diagnose
from netwatch.remediate import remediate


def diamond():
    t = Topology()
    t.add_link("A", "B", 1)
    t.add_link("B", "D", 1)
    t.add_link("A", "C", 5)
    t.add_link("C", "D", 5)
    return t


class SPFTests(unittest.TestCase):
    def test_shortest_path_next_hop(self):
        t = diamond()
        fh = spf(t, "A", set(t.cost))
        self.assertEqual(fh["D"], "B")
        self.assertEqual(fh["C"], "C")      # direct cost 5 beats A-B-D-C (7)

    def test_reroutes_when_link_withdrawn(self):
        t = diamond()
        believed = set(t.cost) - {("B", "D")}
        self.assertEqual(spf(t, "A", believed)["D"], "C")

    def test_unreachable_destination_has_no_route(self):
        t = diamond()
        believed = set(t.cost) - {("B", "D"), ("C", "D")}
        self.assertNotIn("D", spf(t, "A", believed))


class MonitorTests(unittest.TestCase):
    def test_healthy_network_fully_reachable(self):
        t = random_topology(15, 10, seed=3)
        res = probe_all(t, build_fibs(t, set(t.cost)))
        self.assertEqual(summarize(res)["failed"], 0)

    def test_stale_fib_blackholes_after_failure(self):
        t = diamond()
        fibs = build_fibs(t, set(t.cost))
        t.set_state("B", "D", False)
        status, path = trace(t, fibs, "A", "D")
        self.assertEqual(status, BLACKHOLE)
        self.assertEqual(path, ["A", "B"])

    def test_loop_detected_with_inconsistent_fibs(self):
        t = diamond()
        fibs = build_fibs(t, set(t.cost))
        fibs["A"]["D"] = "B"
        fibs["B"]["D"] = "A"        # deliberately inconsistent tables
        self.assertEqual(trace(t, fibs, "A", "D")[0], LOOP)


class RCAAndRemediationTests(unittest.TestCase):
    def setUp(self):
        self.t = random_topology(20, 15, seed=11)
        self.fibs = build_fibs(self.t, set(self.t.cost))
        self.base = probe_all(self.t, self.fibs)

    def test_rca_ranks_failed_link_first(self):
        link = ("r0", "r1")
        self.t.set_state(*link, False)
        broken = probe_all(self.t, self.fibs)
        failed = summarize(broken)["failed_pairs"]
        self.assertTrue(failed)
        ranked = diagnose(self.base, failed)
        self.assertEqual(ranked[0][0], link)

    def test_remediation_restores_reachability(self):
        link = ("r0", "r1")
        self.t.set_state(*link, False)
        broken = probe_all(self.t, self.fibs)
        ranked = diagnose(self.base, summarize(broken)["failed_pairs"])
        withdrawn, _, after, healthy = remediate(self.t, ranked)
        self.assertTrue(healthy)
        self.assertEqual(summarize(after)["failed"], 0)
        self.assertIn(link, withdrawn)


if __name__ == "__main__":
    unittest.main()
