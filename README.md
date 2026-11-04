# Netwatch

Netwatch is a small Python project for exploring how a link-state network behaves when a failure appears before the control plane has fully converged. The idea is simple: routers still forward based on stale routing tables while the real topology has changed, and the system has to detect that mismatch, identify the likely fault, and recover.

It is intentionally narrow and self-contained. There is no external dependency stack, no packet simulator, and no real routing daemon behind it. Instead, the project focuses on the core control-plane/data-plane gap that shows up in real networks: stale forwarding state, blackholes, loops, and diagnosis.

## What it does

- Builds a topology and runs shortest-path routing using an OSPF-like link-state model.
- Generates forwarding tables for each router.
- Probes the network against the live topology while traffic is still using stale forwarding state.
- Classifies failures as `ok`, `blackhole`, `loop`, or `noroute`.
- Uses a simple root-cause analysis step to rank the most likely broken links.
- Withdraws suspect links, recomputes routes, and checks whether reachability is restored.

This makes it useful for understanding the difference between a healthy network and one where the control plane has not caught up yet.

## Why I built it

I wanted a compact way to study network failure detection and remediation without needing a full network emulator. The project is focused on one specific scenario: a link fails, the network remains partially stale, and traffic is still forwarded along paths that no longer match reality.

That is the kind of situation that often produces the most confusing outages in production networks, and it is a good target for experimenting with monitoring and diagnosis.

## Quick start

Run the demo workflow:

```bash
python -m netwatch demo
```

This injects a fault, shows the affected paths, ranks likely causes, and demonstrates remediation.

Run a larger synthetic benchmark:

```bash
python -m netwatch bench
```

This creates a larger topology and runs repeated single-link failure trials.

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

## Example behavior

The project is designed around a pattern like this:

1. A topology is created with routers and links.
2. Each router computes a forwarding table from the current link-state view.
3. A link fails in the real network while the control plane is still unaware.
4. Forwarding still uses the stale table, which can lead to blackholes or loops.
5. The monitor detects failed paths.
6. RCA ranks the suspect links.
7. The remediation step withdraws the most likely failure and re-evaluates the network.

## Benchmark notes

The synthetic benchmark in the project includes repeated single-link failure runs across larger random topologies. In the current simulation, the system performs well in a controlled environment:

- single-link failures are consistently ranked correctly at the top of the RCA output
- remediation restores connectivity in the cases it is expected to fix
- full SPF and forwarding-table construction remains fast on modest-sized topologies

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

This is a simulation, not a production-grade network stack. It is useful for learning and prototyping, but it does not model:

- real BGP or OSPF protocol behavior
- real packet timing or queueing
- ECMP or multi-path routing
- MPLS, tunneling, or transport-layer effects
- noisy telemetry or real-world error distributions

The current implementation is intentionally deterministic and clean, which helps make the failure logic easy to reason about.

## Summary

Netwatch is a compact networking project for exploring how stale routing state leads to failures, how those failures can be detected and explained, and how simple automated remediation can restore service. It is a good fit for someone who wants to work on routing, failure analysis, and network reliability in a small, readable codebase.
