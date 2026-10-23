# HybridPilot supplementary material

**HybridPilot: Crediting Completion Work in Exact Vector–Relational Top-k Queries**

This repository connects the completion protocol, its executable reference,
and the numerical results in the paper. Start with the [paper map](paper-map.md),
then read the [execution contract](docs/execution.md) alongside
[src/completion.py](src/completion.py). The reference executes saved work and
checks each transition against the completion invariants.

## Browse the material

- [Execution contract and implementation boundary](docs/execution.md): state,
  lane ownership, logical closure, scheduling, and finite-progress assumptions.
- [Results and field definitions](results/README.md): all five tables, Figure 2,
  resource and mechanism diagnostics. Values are the paper's aggregate results.
- [Experiment parameters](configs/experiment.json): the large-workload protocol.
- [Example input](examples/query.json) and [computed trace](examples/trace.json).
- [Checks](tests/check_core.py) and [computed check summary](examples/core-checks.json).
- [Figure 1](figures/episodes.pdf) and [Figure 2](figures/accounting.pdf).
- [Readable result tables](results/tables.md), generated from the CSV files.

## Run the small reference

Use Python 3.10 or newer. The commands below require only its standard library.
Run from this repository's root; outputs may be redirected to any writable path.

```text
python analysis/run_example.py --input examples/query.json --policy hybrid --output example-trace.json
python tests/check_core.py --output core-checks.json
python analysis/analyze_results.py --output result-tables.md
```

The first command computes an exact top-1 completion trace for the supplied
integer-distance instance. Change the input distances, eligibility labels, or
witness lengths to inspect other executions. The `mixed`, `vector`, and
`relational` policies exercise alternative legal schedules; `hybrid` uses
provisional gain/time rates and logical closure; cumulative retains all own-lane gain/time with matched initial pseudototals. Eligibility is consulted by
an operator only after its saved witness cursor reaches completion. The oracle
uses all labels to check the final answer.

The checks execute 2,500 finite instances across five scheduling modes and
verify exact answers, monotone completion counts, single attribution of gains,
the two-ID admission bound, saved-work progress, and invariance under extra
yields on an unchanged primitive trace. Focused checks cover cancellation,
conditional residual work, ties, buffered positives, and the 18-versus-2 example.
The JSON outputs report the executions performed by these commands.

The analysis command checks table row counts, selected numeric constraints,
speedup ratios and phase arithmetic, then renders Markdown tables from the
archived CSV values. Field definitions and units are documented separately. It performs result
analysis, not a rerun of the paper's large-workload latency experiments.

## Organization and scope

The executable reference isolates the completion phase with a full top-1 heap,
exact integer distances, four-document blocks and two-document VP cohorts.
The experiment configuration separately records the paper's 64/256-ID units,
vector dimensions, calibration and measurement settings. They are different
execution scales and must not be substituted for each other. See
[execution.md](docs/execution.md) for the relationship to the C++ execution
substrate and the conditional-cost comparisons.

The optional center-envelope diagnostic uses NumPy: python analysis/geometry_bounds.py --output geometry-bounds.csv. It generates 1,800 center/count bounds without full vectors or a DBMS. The reference commands above use only the standard library; no data download, service, or network access is needed.
The repository contains no vendored third-party code. Python and a PDF viewer
are external tools under their respective licenses; no license or artifact
badge from another project is asserted here.
