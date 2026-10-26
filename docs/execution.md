# Execution contract

## Shared state

`completion.run` represents a fixed-snapshot query with distinct integer IDs.
The incumbent `(10, -1)` is already qualified, so the executable starts after
heap filling. Each document has an exact distance and a finite number of
witness advances before a positive witness or complete negative result.
Separate P and R cursors deliberately allow distinct physical paths to reread
witnesses. One path's completed qualification becomes visible to both lanes.

Blocks form a disjoint exhaustive cover. Their admissible lower bounds are
computed before execution and remain fixed. `scored` records distance presence;
`qual` records terminal eligibility. `pending()` contains scored unknowns at
distance at most tau. Unknown unscored IDs contribute to their block count.
`count()` sums those disjoint populations over relevant bounds. Equality is
retained for ID tie breaking. Positive `commit` records eligibility, scoring,
and the heap update atomically. A negative commit makes eligibility terminal.

## Logical work and dispatch

Cohorts and segments are fixed before their first primitive. VP completes
scoring in saved order, then pins its nearest pending consumer until it is
terminal or irrelevant. An R commit can retire that consumer. `normalize`
retires irrelevant positions and closes completed episodes without issuing a
no-op slice. For each executed primitive the code records `before - after`
only in the executing lane's accumulator and records its rational cost.
Suspension contributes neither time nor reward to the suspended lane.

`history` stores exponentially weighted gain/time pairs with alpha=1/4.
At a nonempty closure, `close` performs one update. Empty retirement does not
update history. `hybrid` compares `(3G+a)/(3T+b)` for executed open work and
`G/T` for a lane with no accumulated work. Equal rates retain the current lane;
startup favors R. The loop always executes a runnable finite position, even
when immediate gain is zero. Each trace asserts that the sum of completed and
open gain equals the global decrease. The final answer is checked by exhaustive
qualification and distance/ID ordering, including the incumbent.

The rational costs V=1/3, P=2/3, R=1/2 are **work units**, not milliseconds or
hardware timing estimates. A trace's policy choice can change with these costs.
The model uses one primitive per physical slice. Its replay partitions the same
primitive work into extra yields while retaining commits and episode boundaries,
and verifies equality of the completed EWMA updates. This is distinct from
changing the schedule or charging additional dispatch work.

## Other mechanisms

`survival.remaining` implements the conditional finite stopping-time mean in
Equation 9 from a stopping-count distribution. An exhausted continuation is
rejected. The example with nine probes stopping at 1 and one at 10 gives eight
remaining advances after survival to position 2. The paper's hazard calibration,
backoff, vector histograms and RankBenefit lookahead are described by the
configuration and manuscript; the finite executor supplies the saved-work accounting layer.

`dependency.run` is the Section 4.1 example: 64 IDs in A, 1,000 in B, an incumbent
at distance 10, and a decisive witness at distance 1. Split selection includes
its explicit vector refresh at unit 16. The pooled comparison changes grouping
and consumer-first dispatch together. Its 18/2 work-unit outcomes are not the
factorial comparison in Figure 2.

## Relationship to the system

The executable isolates exact top-1 completion using four-ID blocks,
two-ID cohorts, rational operation costs and saved witness cursors. The
configuration describes the larger vector/join workload with k=10/50/100.
The mathematical stopping argument covers general k through the shared heap
and residual certificate. Focused checks also exercise buffered-positive
ordering and identifier ties.

Finite progress assumes finite saved traversals and successful completion of
access, refinement and I/O. A zero-gain step may consume useful work. The
termination argument is about remaining saved positions, not strict decrease
of the completion count at every step.

## Example input fields

`distances` is a nonempty list of nonnegative integer distances; list positions
are document IDs. `eligible` supplies Boolean ground truth for the finite
witness operator and exhaustive oracle. `witness_advances` supplies positive
integer stopping positions: success for an eligible ID, exhaustive negative
completion otherwise. A zero-witness negative can be represented by one
immediate classification primitive. All three lists have the same length.
The example runner fixes seed 17 for admissible slack in the block bounds and
for mixed-policy scheduling; its block assignment is consecutive groups of four.
The initial incumbent is not a member of those lists. Example results include
that incumbent in the oracle comparison. Costs are exact fraction strings in
JSON; gains and episode indices are integers. `R_resolved_pending` counts pending
IDs removed by R slices, including removals through threshold changes.

## Cumulative and threshold diagnostics
The cumulative selector starts from (12,3), three times the finite work-unit
prior (4,1), and adds each executing lane's gain and time after every primitive.
Logical closure does not reset these totals. Tests verify the final totals
against the event log. The workload calibration pairs are ms-scale aggregates,
not inputs to this finite model.
For threshold attribution, first evaluate the committed state at the old
threshold, then at the new threshold. Their difference is threshold retirement;
the earlier difference from pre-event C is direct retirement. This split is
policy-dependent even though total retirement equals initial C.


For the remaining-cost model, a posting position is an outer record; processing
it searches its inner joins until a qualifying joined witness or exhaustion.
The finite stopping-position calculation in src/survival.py returns expected
remaining positions. In the paper's time model, each survival weight multiplies
the calibrated search cost of that position, including future inner joins.
For an active position, its saved continuation supplies remaining cost in place
of full-position cost. This prevents double charging already executed inner work.
