# Paper-to-material map

| Paper location | Material | Coverage |
|---|---|---|
| Section 2 and Equation 2 | [execution contract](docs/execution.md), [reference](src/completion.py) | Fixed snapshot, admissible exhaustive cover, exact integer distances; large vector/join storage is described in the paper. |
| Section 3, Equations 3–4, Theorem 1 | [reference](src/completion.py), [checks](tests/check_core.py) | Disjoint Q/u state, atomic commits, strict threshold relevance, exact top-1 completion checked against an oracle. |
| Section 4.1 and Section 5.3 | [attribution replay](analysis/replay_attribution.py), [result](results/attribution_replay.json) | Figure 1 states, next selection under both credit rules, and separate histories with partial credit. |
| Section 4.2, Equation 5 | [boundary_tests](src/completion.py) | 4 versus 4.25 physical EWMA; cancellation retains executed cost. |
| Section 5, Algorithm 1, Equations 5–6 | [reference](src/completion.py), [example trace](examples/trace.json) | Fixed units, saved cursors, pinned probe, own-lane gain/time, provisional rates and logical closure. Completion phase only. |
| Proposition 2 | [checks](tests/check_core.py) | Conservation and yield subdivision replay on fixed primitive traces. |
| Proposition 3 | [reference](src/completion.py) | Every step advances saved work; finite-step bound checked. |
| Figure 1 | [figure](figures/episodes.pdf), [editable SVG](figure_sources/episodes.svg), [execution contract](docs/execution.md) | Candidate transfer, alternative credit paths, and pruning after the threshold drops. |
| Section 6.2, Equation 9 | [survival estimator](src/survival.py), [configuration](configs/experiment.json) | Finite conditional residual-work calculation; calibration design parameters. |
| Section 6.4 | [probe-order replay](analysis/check_probe_order.py), [results](results/probe_order_results.json) | Saved-cursor layouts and exact expected work for legal continuations. |
| Section 6.3 | [configuration](configs/experiment.json) | RankBenefit lookahead count and shared model settings; not a full lookahead engine. |
| Table 1 / Section 7.1 | [workloads](results/workloads.csv), [configuration](configs/experiment.json) | Family scales, residual geometry, workload and execution settings. |
| Table 3 | [latencies](results/latency.csv), [analysis](analysis/analyze_results.py) | All 18 policy/family rows and derived speedups. |
| Section 7.4 | [mechanism groups](results/regimes.csv) | Separate targeted groups; negative-regime comparisons remain in the paper. |
| Figure 2(a) | [factorial results](results/accounting.csv), [figure](figures/accounting.pdf), [plot script](figure_sources/plot_accounting.py) | Four matched grouping and update combinations at a fixed dispatcher and 1 ms target. |
| Figure 2(b) | [slice results](results/slices.csv), [figure](figures/accounting.pdf) | Three slice targets under joint histories. The 1 ms row repeats the joint points in Figure 2(a). |
| Sections 7.4–7.5 | [diagnostics](results/diagnostics.json), [MovieLens replay](docs/movielens.md) | SQL overlap, open-cost, phase, memory, spill, and cohort summaries. |

Use [field definitions](results/README.md) when comparing aggregation levels.
The executable tests and aggregate result analysis are separate entry points.

| Additional paper location | Material | Coverage |
|---|---|---|
| Table 1 geometry envelope | results/geometry_bounds.csv, analysis/geometry_bounds.py | Direction-independent k=100 upper bound, not full vector execution. |
| Table 2 and prior sensitivity | results/calibration_and_cumulative.json | Absolute coordinate pairs, matched cumulative initialization, sensitivity aggregates. |
| Table 4 | [controls](results/simple_controls.csv) | Fixed paths, one-time selection, separate histories, endpoint credit, and cumulative completion rates. |
| Cumulative control | src/completion.py, tests/check_core.py | Executable finite cumulative selector and matched initial pseudototals. |

| Section 5.4 | analysis/check_response.py, results/response_computed.csv | Exact provisional-rate crossings with open costs. |
| Table 6 / Section 7.3 | results/phase_order.csv, results/phase_order_design.json | Paired unread-witness placement, completion-only geometric means. |

| Table 5 / Section 7.2 | results/main_strata.csv, analysis/check_strata.py | Main-request burden partition, paired ratios and win/tie/loss counts. |
