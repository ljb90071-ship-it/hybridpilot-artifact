"""Check an exact top-1 query on a finite shared-state model, using work units."""

from dataclasses import dataclass, replace
from fractions import Fraction as Q
from functools import cache
import argparse
import json
from pathlib import Path


B, X, Z = range(3)
DISTANCE = (4, 1, 3)
LOWER_BOUND = (1, 1, 2)
INCUMBENT_DISTANCE = 10
ALPHA = Q(1, 4)
POINT, REL = 'VP', 'R'
UNKNOWN, NEGATIVE, POSITIVE = 0, -1, 1


def holds(row):
    in_region, approved = row
    return in_region and approved


def postings(x_size, x_positive):
    # The point path scans document postings; the batch path evaluates the
    # complete region-filtered postings in its fixed document order B, X, Z.
    wrong_region = (False, True)
    rejected = (True, False)
    point = (
        (wrong_region,) * 8 + (rejected,) * 8,
        (wrong_region,) * (x_size - 2) + (rejected, (True, x_positive)),
        (wrong_region,) * 4 + (rejected,) * 4,
    )
    region = tuple(tuple(row for row in rows if row[0]) for rows in point)
    return point, region


@dataclass(frozen=True)
class State:
    # An incumbent in the first block has already been found by a common
    # score and qualifying witness, and V has scored both members of block A.
    point: tuple = (0, 0, 0)
    batch: tuple = (0, 0, 0)
    eligibility: tuple = (UNKNOWN, UNKNOWN, UNKNOWN)
    z_scored: bool = False

    def threshold(self):
        eligible_distances = [d for d, e in zip(DISTANCE, self.eligibility) if e == POSITIVE]
        return min([INCUMBENT_DISTANCE, *eligible_distances])

    def rivals(self):
        bounds = DISTANCE if self.z_scored else (DISTANCE[B], DISTANCE[X], LOWER_BOUND[Z])
        threshold = self.threshold()
        return tuple(
            i for i, bound in enumerate(bounds)
            if self.eligibility[i] == UNKNOWN and bound <= threshold
        )

    def winner(self):
        assert not self.rivals()
        return 'x' if self.eligibility[X] == POSITIVE else 'incumbent'


def set_at(values, index, value):
    return values[:index] + (value,) + values[index + 1:]


def advance(state, lane, postings):
    """Execute one finite advancing operation, with the same access per policy."""
    point, region = postings
    rivals = state.rivals()
    if lane == REL:
        doc = min(rivals)
        cursor_name = 'batch'
        witnesses = region[doc]
    else:
        if X in rivals:
            doc = X  # nearest pending; it stays pinned until it settles
        elif B in rivals:
            doc = B
        else:
            doc = Z
            if not state.z_scored:
                return replace(state, z_scored=True)
        cursor_name = 'point'
        witnesses = point[doc]

    cursor = getattr(state, cursor_name)
    position = cursor[doc]
    positive = holds(witnesses[position])
    next_state = replace(state, **{cursor_name: set_at(cursor, doc, position + 1)})
    if positive or position + 1 == len(witnesses):
        assert doc == X or not positive
        next_state = replace(next_state, eligibility=set_at(
            next_state.eligibility, doc, POSITIVE if positive else NEGATIVE
        ))
    assert len(next_state.rivals()) <= len(rivals)
    return next_state


def evaluate_lane_choices(x_size):
    rows_by_flag = {flag: postings(x_size, flag) for flag in (False, True)}

    def branches(state, lane):
        status = state.eligibility[X]
        choices = (False, True) if status == UNKNOWN else (status == POSITIVE,)
        return tuple(advance(state, lane, rows_by_flag[flag]) for flag in choices)

    @cache
    def policy_cost(state, mode):
        if not state.rivals():
            return Q(0)
        choose_point = mode == POINT or (mode == 'probe_then_R' and state.eligibility[X] == UNKNOWN)
        successors = branches(state, POINT if choose_point else REL)
        return 1 + sum(policy_cost(s, mode) for s in successors) / len(successors)

    @cache
    def optimal(state):
        if not state.rivals():
            return Q(0), ()
        costs = {}
        for lane in (POINT, REL):
            successors = branches(state, lane)
            costs[lane] = 1 + sum(optimal(s)[0] for s in successors) / len(successors)
        cheapest = min(costs.values())
        return cheapest, tuple(lane for lane, cost in costs.items() if cost == cheapest)

    def pure_recost(state):
        return POINT if policy_cost(state, POINT) < policy_cost(state, REL) else REL

    return rows_by_flag, policy_cost, optimal, pure_recost


class EpisodeRates:
    def __init__(self):
        self.history = {POINT: (Q(4), Q(4)), REL: (Q(63), Q(100))}
        self.open = {POINT: (0, 0, 2)}  # block A, gain zero, two scores paid
        self.current = POINT

    def rate(self, lane):
        gain, duration = self.history[lane]
        _, earned, spent = self.open.get(lane, (None, 0, 0))
        return (3 * gain + earned) / (3 * duration + spent)

    def choice(self):
        return max((POINT, REL), key=lambda lane: (self.rate(lane), lane == self.current))

    def commit(self, lane, before, after):
        block = int(min(before.rivals()) == Z)
        active_block, earned, spent = self.open.get(lane, (block, 0, 0))
        assert active_block == block
        gain = len(before.rivals()) - len(after.rivals())
        self.open[lane] = (block, earned + gain, spent + 1)
        self.current = lane
        pending_blocks = {int(doc == Z) for doc in after.rivals()}
        for owner, (open_block, total_gain, total_time) in list(self.open.items()):
            if open_block not in pending_blocks:
                gain, duration = self.history[owner]
                self.history[owner] = (
                    (1 - ALPHA) * gain + ALPHA * total_gain,
                    (1 - ALPHA) * duration + ALPHA * total_time,
                )
                del self.open[owner]


def start_after_prefix(postings):
    # The first VP cohort in the full-heap prefix is the singleton incumbent:
    # its admissible block bound 0 precedes A's 1 and B's 2. One qualification
    # witness settles it. Scoring A in B,X order then opens the pending probe.
    state = State()
    rates = EpisodeRates()
    for _ in range(6):
        assert rates.choice() == POINT
        next_state = advance(state, POINT, postings)
        assert next_state.rivals() == state.rivals()
        rates.commit(POINT, state, next_state)
        state = next_state
    assert state.point[X] == 6 and state.eligibility[X] == UNKNOWN
    assert rates.open[POINT] == (0, 0, 8) and REL not in rates.open
    return state, rates


def execute(state, postings, choose, rates=None):
    path = []
    while state.rivals():
        lane = choose(state)
        next_state = advance(state, lane, postings)
        path.append((lane, len(state.rivals()) - len(next_state.rivals())))
        if rates:
            rates.commit(lane, state, next_state)
        state = next_state
    assert sum(gain for _, gain in path) == 3
    point, region = postings
    qualifying = [
        (DISTANCE[doc], name) for doc, name in ((B, 'y'), (X, 'x'), (Z, 'z'))
        if any(map(holds, point[doc]))
    ]
    expected = min([(INCUMBENT_DISTANCE, 'incumbent'), *qualifying])[1]
    assert all(any(map(holds, raw)) == any(map(holds, filtered)) for raw, filtered in zip(point, region))
    assert state.winner() == expected
    return {'work': len(path), 'first': path[0][0], 'answer': expected}


def validate():
    for distance, bound in zip(DISTANCE, LOWER_BOUND):
        assert distance >= bound
    output = []
    for x_size in (9, 13):
        rows, cost, optimum, recost = evaluate_lane_choices(x_size)
        state, rates = start_after_prefix(rows[False])
        assert rates.rate(POINT) == Q(3, 5) and rates.rate(REL) == Q(63, 100)
        assert cost(State(), REL) == 12
        assert cost(State(), 'probe_then_R') == x_size + 6 > cost(State(), REL)

        remaining = x_size - state.point[X]
        vp_pure = cost(state, POINT)
        r_first = cost(state, REL)
        probe_first = cost(state, 'probe_then_R')
        assert vp_pure == remaining + Q(25, 2)
        assert r_first == 12 and probe_first == remaining + 6
        optimal_cost, optimal_first = optimum(state)
        assert optimal_cost == min(r_first, probe_first)
        assert optimal_first == ((POINT,) if remaining < 6 else (REL,))

        by_outcome = {}
        for flag, witnesses in rows.items():
            chosen_state, chosen_rates = start_after_prefix(witnesses)
            assert chosen_state == state  # hidden outcome cannot alter the saved state
            by_outcome['positive' if flag else 'negative'] = {
                'r_only': execute(state, witnesses, lambda _: REL),
                'vp_only': execute(state, witnesses, lambda _: POINT),
                'probe_then_r': execute(state, witnesses, lambda s: POINT if s.eligibility[X] == UNKNOWN else REL),
                'pure_path_recost': execute(state, witnesses, recost),
                'episode_rates': execute(state, witnesses, lambda _: chosen_rates.choice(), chosen_rates),
                'optimal': execute(state, witnesses, lambda s: optimum(s)[1][0]),
            }
        policies = by_outcome['positive']
        means = {name: Q(sum(row[name]['work'] for row in by_outcome.values()), 2) for name in policies}
        assert means == {
            'r_only': r_first, 'vp_only': vp_pure, 'probe_then_r': probe_first,
            'pure_path_recost': r_first, 'episode_rates': r_first, 'optimal': optimal_cost,
        }
        assert all(row['pure_path_recost']['first'] == row['episode_rates']['first'] == REL for row in by_outcome.values())
        output.append({
            'point_posting_length': x_size, 'known_unread_point_positions': remaining,
            'paid_point_positions': 6, 'paid_score_units': 2, 'competitor_count': len(state.rivals()),
            'point_rate': str(rates.rate(POINT)), 'relational_rate': str(rates.rate(REL)),
            'unstarted_probe_then_R_cost_at_end_of_scoring': str(cost(State(), 'probe_then_R')),
            'expected_work_from_checkpoint': {name: str(mean) for name, mean in means.items()},
            'optimal_first_lane': optimal_first[0], 'reachable_decision_states_checked': optimum.cache_info().currsize,
            'observed_fixture_branches': by_outcome,
        })
    return output


if __name__ == '__main__':
    results = validate()
    output = {
        'unit': 'one witness test or one distance score; cost starts at replay checkpoint',
        'scope': 'finite exact top-1 replay with rational work units',
        'positive_probability': '1/2', 'r_work_before_x': 8, 'r_work_on_x': 2, 'r_fallback_on_z': 4,
        'cases': results,
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    for case in results:
        print(f"PASS: unread={case['known_unread_point_positions']}, first={case['optimal_first_lane']}, "
              f"work={case['expected_work_from_checkpoint']}, states={case['reachable_decision_states_checked']}")
