# HybridPilot supplementary material

**HybridPilot: Crediting Completion Work in Exact Vector–Relational Top-k Queries**

HybridPilot credits completed dependent work to the lane that performed it,
while keeping unfinished work visible in scheduling decisions. Follow the
mechanism through saved-work completion traces, invariant checks and result
tables, starting with the [paper map](paper-map.md).

## Navigate

- [Execution contract](docs/execution.md): state, lane ownership, logical closure, scheduling and finite-progress assumptions.
- [Implementation](src/completion.py): completion state and scheduling policies.
- [Results and field definitions](results/README.md): aggregate tables, resource accounting and mechanism diagnostics.
- [Experiment parameters](configs/experiment.json): workload, calibration and measurement settings.
- [Example input](examples/query.json) and [computed trace](examples/trace.json).
- [Checks](tests/check_core.py) and [check summary](examples/core-checks.json).
- [Figure 1](figures/episodes.pdf), [Figure 2](figures/accounting.pdf), and [readable result tables](results/tables.md).

## Run

Use Python 3.10 or later and its standard library. Run from the repository root;
output paths may be changed to any writable location.

```text
python analysis/run_example.py --input examples/query.json --policy hybrid --output example-trace.json
python tests/check_core.py --output core-checks.json
python analysis/analyze_results.py --output result-tables.md
```

The example computes an exact top-1 completion trace from integer distances,
eligibility labels and witness lengths. `mixed`, `vector` and `relational`
exercise alternative legal schedules. `hybrid` uses provisional gain/time rates
and logical closure; `cumulative` retains own-lane gain/time with matched initial
pseudototals. An operator consults eligibility after its saved witness cursor
completes; the answer oracle uses all labels.

The checks cover 2,500 instances across five scheduling modes: exact answers,
monotone completion counts, single gain attribution, the two-ID admission bound,
saved-work progress and invariance under extra yields on an unchanged primitive
trace. Focused cases cover cancellation, conditional residual work, ties,
buffered positives and the 18-versus-2 example. Both commands write JSON.

## Analyze results and geometry

`analyze_results.py` checks row counts, numeric constraints, speedup ratios and
phase arithmetic, then renders Markdown tables from aggregate CSV values.
The [result dictionary](results/README.md) defines fields and units.

The completion example uses a full top-1 heap, four-document blocks and
two-document VP cohorts. `configs/experiment.json` records the paper's 64/256-ID
units and vector settings. The [execution guide](docs/execution.md) explains the
relationship between these configurations and the C++ execution substrate.

The optional center-envelope diagnostic requires NumPy:

```sh
python analysis/geometry_bounds.py --output geometry-bounds.csv
```

It computes 1,800 center/count bounds from the stated geometry and writes CSV.
