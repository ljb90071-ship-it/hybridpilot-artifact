# HybridPilot supplementary material

**HybridPilot: Crediting Completion Work in Exact Vector–Relational Top-k Queries**

HybridPilot credits completed dependent work to the lane that performed it,
while keeping unfinished work visible in scheduling decisions. The matched replay shows how changing credit alone can change the next path.
The saved probe comparison follows two different unread posting lengths from
the same observed rates. Follow these examples and the workload comparisons
using the [paper map](paper-map.md).

## Navigate

- [Execution contract](docs/execution.md): state, lane ownership, logical closure, scheduling and finite-progress assumptions.
- [Implementation](src/completion.py): completion state and scheduling policies.
- [Results and field definitions](results/README.md): aggregate tables, resource accounting and mechanism diagnostics.
- [Experiment parameters](configs/experiment.json): workload, calibration and measurement settings.
- [Example input](examples/query.json) and [computed trace](examples/trace.json).
- [Checks](tests/check_core.py) and [check summary](examples/core-checks.json).
- [Figure 1](figures/episodes.pdf), [Figure 2](figures/accounting.pdf), and [readable result tables](results/tables.md).

## Recreate the figures

The [Figure 1 SVG](figure_sources/episodes.svg) holds the candidate transitions,
heap, and threshold axis as editable vectors. Its
[transparent page component](figure_sources/components/block_page.png) comes
from the ImageGen asset collection `Iceberg_数据页与证据覆片/data.png` and
represents the backing page of block A. Figure 2 reads the
[grouping comparison](results/accounting.csv) and the [slice sweep](results/slices.csv).
Both panels use the same 100–145 ms scale. The shaded 1 ms row repeats the
joint-history points from the grouping comparison.

Run from the repository root with CairoSVG for Figure 1 and Matplotlib for Figure 2.

~~~sh
python figure_sources/export_episodes.py
python figure_sources/plot_accounting.py --results results
~~~

## Run

Use Python 3.10 or later and its standard library. Run from the repository root;
output paths may be changed to any writable location.

```text
python analysis/run_example.py --input examples/query.json --policy hybrid --output example-trace.json
python tests/check_core.py --output core-checks.json
python analysis/analyze_results.py --output result-tables.md
python analysis/check_strata.py
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
buffered positives and a producer-refresh case. Both commands write JSON.

## Analyze results, response, and geometry

`analyze_results.py` checks row counts, numeric constraints, speedup ratios and
phase arithmetic, then renders Markdown tables from aggregate CSV values.
The [result dictionary](results/README.md) defines fields and units.
The [main-request partition](results/main_strata.csv) locates gains by qualification
burden and retains paired wins, ties, and losses against AutoCost and Cumulative.

The completion example uses a full top-1 heap, four-document blocks and
two-document VP cohorts. `configs/experiment.json` records the paper's 64/256-ID
units and vector settings. The [execution guide](docs/execution.md) explains the
relationship between these configurations and the C++ execution substrate.

The optional center-envelope diagnostic requires NumPy:

```sh
python analysis/geometry_bounds.py --output geometry-bounds.csv
```

It computes 1,800 center/count bounds from the stated geometry and writes CSV.

The response calculation checks rate crossovers at physical yields, including
unfinished costs and gain commits at closure:

~~~sh
python analysis/check_response.py
~~~

It writes exact rational results to results/response_computed.csv and JSON.
The [paired witness-order comparison](results/phase_order.csv) and its
[design](results/phase_order_design.json) isolate early versus late qualifying
witnesses while preserving query answers. Figure 1 follows the same candidate
from scoring to the heap and shows the work credited to each alternative path.


## Replay credit and the saved probe

Run these standard-library checks from the repository root:

~~~sh
python analysis/replay_attribution.py --output attribution-replay.json
python analysis/check_probe_order.py --output probe-order-results.json
~~~

The first script replays Figure 1 and compares the next decision under two
credit rules. It also checks partial credit for a near score against joint
score-and-probe history. The second enumerates legal continuations from two
saved top-1 states. Output costs are exact work units.

[MovieLens 100K replay](docs/movielens.md) gives the SQLite query protocol,
the official data link, and the attribution and native SQL score counts.
