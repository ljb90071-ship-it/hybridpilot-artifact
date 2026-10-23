# Result schema and aggregation

These files contain the aggregate results used in the paper. They are inputs
to result analysis and figure/table inspection, not per-query timing logs.
The small reference traces in `../examples/` have a separate work-unit scale.

| File | Meaning and units |
|---|---|
| workloads.csv | Table 1. documents is an integer count; dimensions/relations/fanout are counts; radius is the vector generator's radius parameter; relevant_blocks_envelope_upper_pct is the median direction-independent k=100 upper-bound percentage over 4096 blocks (not the exact-threshold percentage); entry_Q_over_u is the median initial contribution ratio; threshold_removals_pct pools HybridPilot threshold-only retirements divided by pooled initial post-prefix C over C>0 requests, after direct commits at the old threshold. |
| latency.csv | Table 3. queries=600 per family. geomean_ms and p95_ms aggregate per-query median elapsed time across five runs after one warm-up. Policies include online preparation, planning, scoring, qualification, refinement, metadata, spill service and final sorting. |
| regimes.csv | Table 5. Each independent group has 60 queries; all three policy columns are geometric-mean milliseconds. These are not a partition of Table 3. Cost/Benefit in the paper mean AutoCost/RankBenefit here. |
| accounting.csv | Figure 2(a). 120 Media states, same within-lane dispatch rules. Separate/joint grouping crossed with physical/logical updates; geomean_ms is completion time. |
| slices.csv | Figure 2(b). The same 120 states with joint credit, three target physical slice budgets in ms. Both response columns are completion-time geometric means in ms. |
| diagnostics.json | Media phase arithmetic means, memory medians in MiB, spill and cohort geometric means in ms, maintenance arithmetic means, and separate overlap/long-probe groups. Each field names its unit/aggregation. |

Geometric means are not additive. Only `phase_arithmetic_means_ms` is used for
prefix + completion = total checks. p95 is not a confidence interval. No
per-query records or error bars are inferred from these summaries. Setup index
and calibration time is excluded from query latency; the setup times reported
in Section 7.1 are 91/84/129 seconds for Catalog/Documents/Media.

Figure 1 is a schematic execution order, not a measured time axis. Figure 2(b)
uses a base-4 logarithmic budget axis and an explicitly labeled nonzero response
axis; the left bar plot begins at zero. The fixed-trace partition identity does
not assert that changing a runtime slice budget preserves latency.

## Added completion controls and geometry

simple_controls.csv supplies Table 4: 15 policy/family rows, 600 requests each,
full-query geometric-mean ms. VP-only and R-only commit to a complete path;
OnceCost chooses once at the shared prefix boundary. Cumulative uses the same
own-slice attribution and grouping as HybridPilot with no forgetting.

calibration_and_cumulative.json supplies Table 2 (absolute mean gain/time
pairs from 128 calibration states per family), the 120-state Media completion
comparison (109 versus 106 geometric-mean ms), and full-query prior-strength
sensitivity. Gains count competitors and times are ms; VP equals V+P coordinate
wise. Both prior coordinates are multiplied by s; cumulative pseudototals are
3s times the pair, matching alpha=0.25 before the first episode closes.
These pairs do not replace the finite reference's work-unit prior (4,1).

geometry_bounds.csv contains 1,800 generated center/count diagnostics, 600 per
family. any_direction_k100_upper_pct is the Table 1 statistic. It uses a
query perturbation envelope 0.3r and vector radius envelope 1.02r+0.0001.
With center distances d_j from the selected query microcenter, j* is the
sorted prefix first containing 100 eligible IDs. Tau is bounded by
d_j*+delta+R; blocks with d_j-delta-R larger than that value are excluded.
Each percentage uses all 4096 blocks as denominator. Lower k and the actual
query direction can only improve the bound. This is a center/count computation,
not an observed final-threshold measurement or latency experiment.
The script records the generated k and assignment mode and fixes seed streams
10/20/30 for geometry/requests/eligibility counts, with salt 0.

The overlap diagnostic's 23 percent means direct terminal qualifications by R
among admitted near candidates; threshold-only retirements are excluded.
The finite reference exposes threshold retirements separately and tests their
policy dependence on a two-ID instance (vector 1/2, relational 0).
