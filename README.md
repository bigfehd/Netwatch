# Netwatch

Netwatch is a small Python project I built to study how a network behaves when a link fails before the control plane has fully converged. In that situation, routers can still forward traffic using stale forwarding tables, which leads to blackholes, loops, and broken reachability even though the topology has already changed.

The project focuses on that gap between the control plane and the data plane: detecting the failure, explaining what likely caused it, and testing a simple remediation path.

## The problem it explores

In real networks, outages do not always appear as a clean, instantaneous event. There is often a brief period where the routing state is inconsistent with the current physical topology.

This matters because traffic can still be forwarded according to earlier decisions, even if a link has already gone down. That can produce:

- blackholes, where packets disappear because the next hop is no longer valid
- loops, where the forwarding path cycles without reaching the destination
- partial reachability loss, where some destinations fail while others continue to work

Netwatch models a simplified version of that behavior and tries to detect and explain it.

## What the project does

- builds a network topology and computes shortest-path forwarding tables
- simulates link failures while the control plane is still stale
- probes the network to detect traffic that is no longer reaching its destination
- classifies the failed paths as `ok`, `blackhole`, `loop`, or `noroute`
- ranks the most likely failed links using a root-cause analysis step
- removes suspect links and checks whether the network recovers after reconvergence

This is intentionally limited and readable. It is not trying to be a full production routing stack; it is trying to make a specific networking problem easy to reason about.

## Why this is interesting

I wanted a project that sits close to the kind of problems network engineers deal with every day: routing correctness, fault localization, and recovery after a failure. A lot of the work in network operations is less about raw throughput and more about understanding what failed, why traffic is taking the wrong path, and how to restore service quickly.

This project is a small version of that mindset.

## Quick start

Run the demo flow:

```bash
python -m netwatch demo
```

This shows a single injected failure, prints the failed probes, ranks the likely cause, and demonstrates remediation.

Run a larger synthetic benchmark:

```bash
python -m netwatch bench
```

This generates a larger topology and runs repeated single-link failure experiments.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Example flow

1. A topology is built with routers and links.
2. Each router computes a forwarding table from the current link-state view.
3. A link fails in the real network while the control plane is still unaware.
4. Traffic continues to use stale forwarding entries.
5. The monitor identifies broken paths.
6. The RCA step ranks the most likely failing links.
7. The remediation process withdraws the suspect link and checks whether connectivity is restored.

## Benchmark notes

The project includes a benchmark that runs repeated single-link failure trials on larger random topologies. In the simulation, the system performs well under controlled conditions:

- the true failing link is usually ranked first by the RCA step
- remediation restores reachability in the cases it is designed to heal
- SPF and forwarding-table construction remain fast for moderate network sizes

## Project structure

```text
netwatch/
├── __init__.py
├── __main__.py
├── monitor.py
├── rca.py
├── remediate.py
├── spf.py
├── topology.py
└── tests/
    └── test_netwatch.py
```

## Limits

This is a simulation, not a production routing platform. It is useful for learning and experimentation, but it does not model:

- real OSPF or BGP protocol behavior
- packet timing, queueing, or real network loss patterns
- ECMP or multi-path routing
- MPLS, tunneling, or transport-layer behavior
- noisy telemetry or real-world operational complexity

That is intentional. The project is meant to be clear and focused rather than trying to simulate an entire network stack.

## Summary

Netwatch is a compact networking project for exploring stale forwarding state, failure detection, and automated recovery in a simplified link-state environment. It is not a massive platform, but it is a solid example of systems thinking in networking: observe the behavior, reason about the failure, and test a recovery strategy.
