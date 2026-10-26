# Paper-to-material map

| Paper location | Material | Coverage |
|---|---|---|
| Section 2 and Equation 2 | [execution contract](docs/execution.md), [reference](src/completion.py) | Fixed snapshot, admissible exhaustive cover, exact integer distances; large vector/join storage is described in the paper. |
| Section 3, Equations 3–4, Theorem 1 | [reference](src/completion.py), [checks](tests/check_core.py) | Disjoint Q/u state, atomic commits, strict threshold relevance, exact top-1 completion checked against an oracle. |
| Section 4.1 | [dependency example](src/dependency.py) | Actual action selection and counter evolution for 18 versus 2 work units. |
| Section 4.2, Equation 5 | [boundary_tests](src/completion.py) | 4 versus 4.25 physical EWMA; cancellation retains executed cost. |
| Section 5, Algorithm 1, Equations 5–6 | [reference](src/completion.py), [example trace](examples/trace.json) | Fixed units, saved cursors, pinned probe, own-lane gain/time, provisional rates and logical closure. Completion phase only. |
| Proposition 2 | [checks](tests/check_core.py) | Conservation and yield subdivision replay on fixed primitive traces. |
| Proposition 3 | [reference](src/completion.py) | Every step advances saved work; finite-step bound checked. |
| Figure 1 | [figure](figures/episodes.pdf), [execution contract](docs/execution.md) | Score-to-probe grouping and alternative R completion with distinct lane attribution. |
| Section 6.2, Equation 9 | [survival estimator](src/survival.py), [configuration](configs/experiment.json) | Finite conditional residual-work calculation; calibration design parameters. |
| Section 6.3 | [configuration](configs/experiment.json) | RankBenefit lookahead count and shared model settings; not a full lookahead engine. |
| Table 1 / Section 7.1 | [workloads](results/workloads.csv), [configuration](configs/experiment.json) | Family scales, residual geometry, workload and execution settings. |
| Table 3 | [latencies](results/latency.csv), [analysis](analysis/analyze_results.py) | All 18 policy/family rows and derived speedups. |
| Section 7.4 | [mechanism groups](results/regimes.csv) | Separate targeted groups; negative-regime comparisons remain in the paper. |
| Figure 2(a) | [factorial results](results/accounting.csv), [figure](figures/accounting.pdf) | Four cells, fixed dispatcher. |
| Figure 2(b) | [slice results](results/slices.csv), [figure](figures/accounting.pdf) | All six values with budget and units. |
| Sections 7.4–7.5 | [diagnostics](results/diagnostics.json) | Overlap, open-cost, phase, memory, spill and cohort summaries. |

Use [field definitions](results/README.md) when comparing aggregation levels.
The executable tests and aggregate result analysis are separate entry points.

| Additional paper location | Material | Coverage |
|---|---|---|
| Table 1 geometry envelope | results/geometry_bounds.csv, analysis/geometry_bounds.py | Direction-independent k=100 upper bound, not full vector execution. |
| Table 2 and prior sensitivity | results/calibration_and_cumulative.json | Absolute coordinate pairs, matched cumulative initialization, sensitivity aggregates. |
| Table 4 | results/simple_controls.csv | Fixed paths, one-time selection, cumulative and episode rates. |
| Cumulative control | src/completion.py, tests/check_core.py | Executable finite cumulative selector and matched initial pseudototals. |

| Section 5.4 | analysis/check_response.py, results/response_computed.csv | Exact provisional-rate crossings with open costs. |
| Table 6 / Section 7.3 | results/phase_order.csv, results/phase_order_design.json | Paired unread-witness placement, completion-only geometric means. |

| Table 5 / Section 7.2 | results/main_strata.csv, analysis/check_strata.py | Main-request burden partition, paired ratios and win/tie/loss counts. |
