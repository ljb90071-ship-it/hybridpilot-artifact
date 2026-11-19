"""Replay the matched attribution comparison in Sections 4 and 5.

The executor uses exact distances, deterministic blocks and rational work costs.
Each step is a safe slice. Only the gain credited to an episode varies.
"""
import argparse
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path


@dataclass(frozen=True)
class Document:
    name: str
    distance: int
    eligible: bool = False


BLOCKS = (
    (0, (Document('x', 4, True), Document('y', 8), Document('z', 9))),
    (1, (Document('u', 3), Document('v', 1, True))),
    (5, tuple(Document(f'b{i}', 6) for i in range(1, 6))),
)
INCUMBENT = Document('incumbent', 10, True)
DOCS = {doc.name: doc for _, block in BLOCKS for doc in block}
LANES = ('VP', 'R')


@dataclass
class Episode:
    block: int
    initial_count: int
    gain: int = 0
    time: int = 0


class Replay:
    def __init__(self, credit):
        self.credit = credit
        self.scored = set()
        self.qualified = set()
        self.best = INCUMBENT
        self.open = {}
        self.history = {'VP': (Fraction(4), Fraction(1)),
                        'R': (Fraction(6), Fraction(2))}
        self.credits = []
        self.trace = []
        self.last = 'R'

    def remaining(self, block_index):
        bound, docs = BLOCKS[block_index]
        return [doc for doc in docs if doc.name not in self.qualified and
                (doc.distance if doc.name in self.scored else bound) <= self.best.distance]

    def count(self):
        return sum(len(self.remaining(i)) for i in range(len(BLOCKS)))

    def rate(self, lane):
        gain, time = self.history[lane]
        episode = self.open.get(lane)
        if episode is None:
            return gain / time
        return (3 * gain + self.gain(episode)) / (3 * time + episode.time)

    def gain(self, episode):
        if self.credit == 'endpoints':
            return episode.initial_count - self.count()
        return episode.gain

    def choice(self):
        return max(LANES, key=lambda lane: (self.rate(lane), lane == self.last))

    def commit(self, doc):
        self.qualified.add(doc.name)
        if doc.eligible:
            self.scored.add(doc.name)
            self.best = min((self.best, doc), key=lambda item: (item.distance, item.name))

    def execute(self, lane):
        before = self.count()
        if lane not in self.open:
            block = next(i for i in range(len(BLOCKS)) if self.remaining(i))
            self.open[lane] = Episode(block, before)
        episode = self.open[lane]
        names = []
        if lane == 'VP':
            unscored = [doc for doc in self.remaining(episode.block) if doc.name not in self.scored]
            if unscored:
                names = [doc.name for doc in unscored]
                self.scored.update(names)
                op, work = 'score', 2  # one vector batch of at most three objects
            else:
                doc = min(self.remaining(episode.block), key=lambda item: (item.distance, item.name))
                self.commit(doc)
                op, work, names = 'probe', 1, [doc.name]
        else:
            op, work = 'qualify', 0
            for doc in BLOCKS[episode.block][1]:
                if doc not in self.remaining(episode.block):
                    continue
                work += 1 + (doc.eligible and doc.name not in self.scored)
                names.append(doc.name)
                self.commit(doc)
        after = self.count()
        assert 0 <= after <= before and work > 0
        episode.gain += before - after
        episode.time += work
        for closing_lane, closed in list(self.open.items()):
            if not self.remaining(closed.block):
                gain = self.gain(closed)
                old_gain, old_time = self.history[closing_lane]
                self.history[closing_lane] = ((3 * old_gain + gain) / 4,
                                              (3 * old_time + closed.time) / 4)
                self.credits.append({'lane': closing_lane, 'gain': gain, 'time': closed.time})
                del self.open[closing_lane]
        self.trace.append({'lane': lane, 'operation': op, 'identifiers': names,
                           'work': work, 'count': after, 'threshold': self.best.distance})
        self.last = lane

    def signature(self):
        return self.best, self.scored, self.qualified, self.count()


def compare():
    own, endpoints = (Replay(rule) for rule in ('own_slice', 'endpoints'))
    for replay in (own, endpoints):
        assert replay.choice() == 'VP'
        replay.execute('VP')
        assert replay.count() == 10 and replay.choice() == 'R'
    point = deepcopy(own)
    point.execute('VP')
    assert point.credits == [{'lane': 'VP', 'gain': 8, 'time': 3}]
    for replay in (own, endpoints):
        replay.execute('R')
    assert own.trace == endpoints.trace
    assert own.signature() == endpoints.signature() == point.signature()
    assert own.count() == 2 and not own.open and not endpoints.open
    assert [sum(e['gain'] for e in r.credits) for r in (own, endpoints)] == [8, 16]
    assert own.rate('VP') == Fraction(12, 5) and endpoints.rate('VP') == 4
    assert own.rate('R') == endpoints.rate('R') == Fraction(26, 7)
    assert own.choice() == 'R' and endpoints.choice() == 'VP'
    result = {'probe_alternative': point.credits, 'checkpoint_count': own.count()}
    for replay in (own, endpoints):
        checkpoint = {'rates': {lane: str(replay.rate(lane)) for lane in LANES},
                      'choice': replay.choice(), 'credits': replay.credits.copy()}
        while replay.count():
            assert len(replay.trace) < 6
            replay.execute(replay.choice())
        assert replay.best == min((d for d in DOCS.values() if d.eligible), key=lambda d: d.distance)
        checkpoint.update(answer=replay.best.name, trace=replay.trace,
                          remaining_work=sum(e['work'] for e in replay.trace[2:]))
        result[replay.credit] = checkpoint
    assert [result[rule]['remaining_work'] for rule in ('own_slice', 'endpoints')] == [3, 4]
    return result


def check_pending_weight():
    """Compare separate histories using C_theta with a joint VP history.

    Use the x/y/z block and the excluded block B, omitting the later block D.
    R checks y, z, then x at two work units each. V costs two and P costs one.
    The VP calibration uses the same completed score-and-probe work.
    """
    rows = []
    for r_initial in (Fraction(2), Fraction(1)):
        for theta in (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1)):
            # Once V runs, x, y and z move to pending; B's five slots stay unscored.
            credit_for_scoring = 8 - (5 + 3 * theta)
            credit_for_probe = 5 + 3 * theta
            assert credit_for_scoring + credit_for_probe == 8
            score_rate = credit_for_scoring / 2
            joint_rate = Fraction(8, 3)
            joint_after_score = Fraction(24, 11)  # HybridPilot uses theta=1
            assert joint_rate > r_initial and joint_after_score > r_initial

            # Calibrated R duration is four. Each earlier R rejection adds one
            # gain and two work units, with the episode open until it reaches x.
            r_rates = [(12 * r_initial + completed) / (12 + 2 * completed)
                       for completed in range(3)]
            if score_rate > r_rates[0]:
                assert credit_for_probe > r_rates[0]
                separate = ['V', 'P']
                work = 3
            else:
                assert all(rate >= score_rate for rate in r_rates)
                separate = ['R', 'R', 'R']
                work = 6
            if r_initial == 2:
                assert min(r_rates) > Fraction(3, 2) >= score_rate
                assert work == 6
            if r_initial == 1 and theta == Fraction(1, 4):
                assert work == 3
            rows.append({'theta': str(theta), 'initial_r_rate': str(r_initial),
                         'separate_score_rate': str(score_rate),
                         'separate_actions': separate, 'separate_work': work,
                         'joint_actions': ['V', 'P'], 'joint_work': 3})
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    results = compare()
    results['pending_weight'] = check_pending_weight()
    output = json.dumps(results, indent=2)
    if args.output:
        args.output.write_text(output + '\n', encoding='utf-8')
    print(output)
