# Result schema and aggregation

These files contain the aggregate results used in the paper. They are inputs
to result analysis and figure/table inspection, not per-query timing logs.
The small reference traces in `../examples/` have a separate work-unit scale.

| File | Meaning and units |
|---|---|
| workloads.csv | Table 1. documents is an integer count; dimensions/relations/fanout are counts; radius is the vector generator's radius parameter; relevant_blocks_envelope_upper_pct is the median direction-independent k=100 upper-bound percentage over 4096 blocks (not the exact-threshold percentage); entry_Q_over_u is the median initial contribution ratio; threshold_removals_pct pools HybridPilot threshold-only retirements divided by pooled initial post-prefix C over C>0 requests, after direct commits at the old threshold. |
| latency.csv | Table 3. queries=600 per family. geomean_ms and p95_ms aggregate per-query median elapsed time across five runs after one warm-up. Policies include online preparation, planning, scoring, qualification, refinement, metadata, spill service and final sorting. |
| regimes.csv | Additional mechanism results. Each independent group has 60 queries; all three policy columns are geometric-mean milliseconds. These are not a partition of Table 3. The paper retains the three negative-regime comparisons in Section 7.4. |
| accounting.csv | Figure 2(a). 120 Media states, same within-lane dispatch rules. Separate/joint grouping crossed with physical/logical updates; geomean_ms is completion time. |
| slices.csv | Figure 2(b). The same 120 states with joint credit, three target physical slice budgets in ms. Both response columns are completion-time geometric means in ms. |
| diagnostics.json | Media phase arithmetic means, memory medians in MiB, spill and cohort geometric means in ms, maintenance arithmetic means, and separate overlap/long-probe groups. Each field names its unit/aggregation. |

Geometric means are not additive. Only `phase_arithmetic_means_ms` is used for
prefix + completion = total checks. p95 is not a confidence interval. No
per-query records or error bars are inferred from these summaries. Setup index
and calibration time is excluded from query latency; the setup times reported
in Section 7.1 are 91/84/129 seconds for Catalog/Documents/Media.

Figure 1 illustrates a 10-to-10-to-2 competitor-count transition. Scoring transfers three IDs to pending qualification; P or R then qualifies one and retires seven through the threshold. P completion yields joint VP gain/time (8,3); R completion yields R (8,1) and canceled VP (0,2). Its times are illustrative work units. Figure 2(b)
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

## Phase response and paired order

response_computed.csv/json is computed by analysis/check_response.py from
exact rational gain/time updates. Its unit is selected-lane work, with gain
committed at each unit's end and decisions at quarter units. N counts completed
old high-gain observations. Both initial rates equal 8, and the alternative
lane's unchanged rate is 4. The first switch includes open execution cost.
The calculation stops at that switch.

phase_order.csv supplies Table 6: completion-time geometric-mean ms for 60
paired Media states in each of two witness-placement variants. Full protocol
and fixed quantities are in phase_order_design.json. These states are separate
from the 120-state accounting comparison and from the 600-request family
totals. Reconstruction is excluded; online policy and execution time is included.


## Main-request qualification burden

main_strata.csv supplies Table 5 and the paired win/tie/loss counts in Section 7.2.
All 600 requests per family are assigned by the qualification share of a fixed
VP-only characterization run from the common-prefix state. Low is b<=1/3,
Middle is 1/3<b<=2/3, High is b>2/3, where b=tP/(tP+tV), or zero for no work.
Setup/selection are excluded from the descriptor; all full-query times include
their ordinary online costs. Characterization execution is separate.

Each baseline_over_hybrid_gm is a paired full-query latency ratio. hybrid_wins
means ratio>1.01, baseline_wins means ratio<1/1.01, and ties cover the closed
interval between these bounds. log_ratio_sum preserves the unrounded aggregate.
For each family/baseline, exp(sum(log_ratio_sum)/600) reproduces its family ratio
from latency.csv or simple_controls.csv. Table 5 rounds ratios to three decimals.
Counts partition requests, not repeated runs; no uncertainty interval is inferred
from these aggregate rows. analysis/check_strata.py checks these relations.
