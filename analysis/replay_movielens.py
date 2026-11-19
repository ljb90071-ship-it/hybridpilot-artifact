#!/usr/bin/env python3
"""Replay one point/batch interleaving on MovieLens 100K using SQLite."""

import argparse
import csv
import hashlib
import json
import sqlite3
import statistics
from contextlib import closing
from pathlib import Path


SOURCE_FILES = ("u.item", "u.user", "u.data")
SEEDS = range(1, 9)
K = 10
COHORT = 64
SEGMENT = 256

POINT = """
SELECT EXISTS (
    SELECT 1 FROM ratings AS r INDEXED BY ratings_movie_stars
    CROSS JOIN reviewers AS u ON u.id = r.user_id
    WHERE r.movie_id = ? AND r.stars = 5 AND u.occupation = ?
)
"""

NATIVE = """
SELECT m.id, squared_l2(m.genres, :profile) AS d2
FROM movies AS m
WHERE m.id <> :seed AND EXISTS (
    SELECT 1 FROM ratings AS r INDEXED BY ratings_movie_stars
    CROSS JOIN reviewers AS u ON u.id = r.user_id
    WHERE r.movie_id = m.id AND r.stars = 5 AND u.occupation = :occupation
)
ORDER BY d2, m.id
LIMIT :k
"""

PREFILTER_JOIN = """
FROM reviewers AS u INDEXED BY reviewer_occupation
CROSS JOIN ratings AS r INDEXED BY ratings_user_stars
    ON r.user_id = u.id AND r.stars = 5
WHERE u.occupation = :occupation AND r.movie_id <> :seed
"""

PREFILTER = f"""
WITH qualified AS MATERIALIZED (
    SELECT DISTINCT r.movie_id {PREFILTER_JOIN}
)
SELECT m.id, squared_l2(m.genres, :profile) AS d2
FROM qualified AS q JOIN movies AS m ON m.id = q.movie_id
ORDER BY d2, m.id
LIMIT :k
"""


def load_source(data_dir):
    raw = {name: (data_dir / name).read_bytes() for name in SOURCE_FILES}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()}
    profiles = {}
    for line in raw["u.item"].decode("latin-1").splitlines():
        fields = line.split("|")
        movie_id = int(fields[0])
        profiles[movie_id] = tuple(map(int, fields[5:]))
    reviewers = {}
    for line in raw["u.user"].decode("ascii").splitlines():
        user_id, _, _, occupation, _ = line.split("|")
        reviewers[int(user_id)] = occupation
    ratings = []
    for line in raw["u.data"].decode("ascii").splitlines():
        user_id, movie_id, stars, _ = map(int, line.split("\t"))
        ratings.append((movie_id, user_id, stars))
    assert len(profiles) == 1682 and set(profiles) == set(range(1, 1683))
    assert all(len(p) == 19 and set(p) <= {0, 1} for p in profiles.values())
    assert len(reviewers) == 943 and len(set(reviewers.values())) == 21
    assert len(ratings) == 100000
    return profiles, reviewers, ratings, hashes


def make_mask(profile):
    return sum(value << index for index, value in enumerate(profile))


class Sql:
    def __init__(self, db, profiles, reviewers, ratings):
        self.db = db
        self.distance_calls = 0
        db.create_function("squared_l2", 2, self.distance, deterministic=True)
        db.executescript("""
            CREATE TABLE movies (id INTEGER PRIMARY KEY, genres INTEGER NOT NULL);
            CREATE TABLE reviewers (id INTEGER PRIMARY KEY, occupation TEXT NOT NULL);
            CREATE TABLE ratings (movie_id INTEGER, user_id INTEGER, stars INTEGER,
                                  PRIMARY KEY (movie_id, user_id));
            CREATE INDEX reviewer_occupation ON reviewers (occupation, id);
            CREATE INDEX ratings_user_stars ON ratings (user_id, stars, movie_id);
            CREATE INDEX ratings_movie_stars ON ratings (movie_id, stars, user_id);
        """)
        db.executemany("INSERT INTO movies VALUES (?, ?)",
                       ((movie_id, make_mask(p)) for movie_id, p in profiles.items()))
        db.executemany("INSERT INTO reviewers VALUES (?, ?)", reviewers.items())
        db.executemany("INSERT INTO ratings VALUES (?, ?, ?)", ratings)
        db.commit()

    def distance(self, bits, query):
        self.distance_calls += 1
        return (bits ^ query).bit_count()

    def scores(self, ids, profile):
        if not ids:
            return []
        marks = ",".join("?" for _ in ids)
        before = self.distance_calls
        rows = self.db.execute(
            f"SELECT id, squared_l2(genres, ?) FROM movies WHERE id IN ({marks})",
            (profile, *ids),
        ).fetchall()
        assert len(rows) == len(ids) == self.distance_calls - before
        return rows

    def batch(self, ids, occupation):
        marks = ",".join("?" for _ in ids)
        return {
            movie_id for (movie_id,) in self.db.execute(f"""
                SELECT DISTINCT r.movie_id
                FROM ratings AS r INDEXED BY ratings_movie_stars
                CROSS JOIN reviewers AS u ON u.id = r.user_id
                WHERE r.movie_id IN ({marks}) AND r.stars = 5 AND u.occupation = ?
            """, (*ids, occupation))
        }

    def static(self, sql, params):
        before = self.distance_calls
        rows = self.db.execute(sql, params).fetchall()
        return rows, self.distance_calls - before


class Completion:
    """One coarse block with lower bound zero and exact nonnegative distances."""

    def __init__(self, sql, ids, seed, profile, occupation):
        self.sql = sql
        self.last_id = max(ids)
        self.profile = profile
        self.occupation = occupation
        self.unscored = set(ids) - {seed}
        self.pending = {}
        self.best = []
        self.vector_cursor = self.rel_cursor = 1
        self.n_scores = self.n_probes = self.n_batches = self.n_batch_ids = 0

    def fork(self):
        other = object.__new__(Completion)
        other.__dict__ = self.__dict__.copy()
        other.unscored = self.unscored.copy()
        other.pending = self.pending.copy()
        other.best = self.best.copy()
        return other

    def count(self):
        return len(self.unscored) + len(self.pending)

    def threshold(self):
        return self.best[-1][0] if len(self.best) == K else 19

    def trim(self):
        self.best = sorted(self.best)[:K]
        cutoff = self.threshold()
        self.pending = {movie_id: d2 for movie_id, d2 in self.pending.items() if d2 <= cutoff}

    def score_cohort(self):
        assert not self.pending
        while self.vector_cursor <= self.last_id:
            start = self.vector_cursor
            self.vector_cursor += COHORT
            ids = [movie_id for movie_id in range(start, self.vector_cursor)
                   if movie_id in self.unscored]
            if not ids:
                continue
            self.unscored.difference_update(ids)
            self.n_scores += len(ids)
            cutoff = self.threshold()
            self.pending = {movie_id: d2 for movie_id, d2 in self.sql.scores(ids, self.profile)
                            if d2 <= cutoff}
            return

    def point(self):
        movie_id = min(self.pending, key=lambda i: (self.pending[i], i))
        d2 = self.pending.pop(movie_id)
        (positive,) = self.sql.db.execute(POINT, (movie_id, self.occupation)).fetchone()
        self.n_probes += 1
        if positive:
            self.best.append((d2, movie_id))
            self.trim()
        return bool(positive)

    def drain(self):
        while self.pending:
            self.point()

    def relational_segment(self):
        while self.rel_cursor <= self.last_id:
            start = self.rel_cursor
            self.rel_cursor += SEGMENT
            ids = [movie_id for movie_id in range(start, self.rel_cursor)
                   if movie_id in self.unscored or movie_id in self.pending]
            if not ids:
                continue
            positives = self.sql.batch(ids, self.occupation)
            fresh = sorted(positives & self.unscored)
            self.n_scores += len(fresh)
            self.n_batches += 1
            self.n_batch_ids += len(ids)
            self.best.extend((d2, movie_id) for movie_id, d2 in self.sql.scores(fresh, self.profile))
            direct = 0
            for movie_id in ids:
                if movie_id in self.pending:
                    d2 = self.pending.pop(movie_id)
                    direct += 1
                    if movie_id in positives:
                        self.best.append((d2, movie_id))
                self.unscored.discard(movie_id)
            before_trim = len(self.pending)
            self.trim()
            return direct, before_trim - len(self.pending)
        return 0, 0

    def fill(self):
        while self.count() and len(self.best) < K:
            self.score_cohort()
            self.drain()
            if self.count() and len(self.best) < K:
                self.relational_segment()

    def exhaust(self):
        while self.count():
            self.drain()
            before = self.count()
            if before:
                self.score_cohort()
                assert self.pending or self.count() < before
        return [(movie_id, d2) for d2, movie_id in self.best]


def run_query(sql, profiles, eligible, seed, occupation):
    profile = profiles[seed]
    qualified = eligible[occupation] - {seed}
    oracle = sorted(
        ((movie_id, sum((a - b) ** 2 for a, b in zip(profile, profiles[movie_id])))
         for movie_id in qualified),
        key=lambda row: (row[1], row[0]),
    )[:K]
    params = {"seed": seed, "profile": make_mask(profile), "occupation": occupation, "k": K}
    native, native_scores = sql.static(NATIVE, params)
    eager, eager_scores = sql.static(PREFILTER, params)
    (witness_rows,) = sql.db.execute("SELECT count(*) " + PREFILTER_JOIN, params).fetchone()
    assert native == eager == oracle
    assert eager_scores == len(qualified)

    shared = Completion(sql, profiles, seed, params["profile"], occupation)
    shared.fill()
    full_heap = len(shared.best) == K
    c_open = shared.count()
    score_prefix = shared.n_scores
    shared.score_cohort()
    c_after_score = shared.count()
    assert c_open >= c_after_score
    pending = len(shared.pending)
    cutoff = shared.threshold()

    point = shared.fork()
    first_positive = point.point() if pending else False
    point_first_gain = c_after_score - point.count()
    cutoff_after_first_point = point.threshold()
    point.drain()
    point_gain = c_after_score - point.count()
    cutoff_after_draining = point.threshold()
    cohort_probe_calls = point.n_probes - shared.n_probes
    assert point.exhaust() == oracle

    relational = shared.fork()
    direct, retired = relational.relational_segment() if pending else (0, 0)
    c_after_r = relational.count()
    r_gain = c_after_score - c_after_r
    cutoff_after_r = relational.threshold()
    assert pending - len(relational.pending) == direct + retired
    if pending:
        assert relational.n_batches == shared.n_batches + 1
    relational.drain()
    c_close = relational.count()
    v_gain = c_open - c_after_score
    vp_owned = v_gain + (c_after_r - c_close)
    vp_window = c_open - c_close
    assert vp_owned + r_gain == vp_window and vp_owned >= 0
    assert relational.exhaust() == oracle

    return {
        "seed": seed, "occupation": occupation, "eligible": len(qualified),
        "full_heap": full_heap, "prefix_scores": score_prefix,
        "c_open": c_open, "c_after_score": c_after_score,
        "cohort_scores": shared.n_scores - score_prefix, "pending": pending,
        "d2_cutoff_after_score": cutoff,
        "point_first_positive": first_positive, "point_first_gain": point_first_gain,
        "d2_cutoff_after_first_point": cutoff_after_first_point,
        "point_first_tightened": cutoff_after_first_point < cutoff,
        "point_drain_gain": point_gain, "point_drain_calls": cohort_probe_calls,
        "d2_cutoff_after_point_drain": cutoff_after_draining,
        "point_drain_tightened": cutoff_after_draining < cutoff,
        "r_direct": direct, "r_threshold_retired": retired, "r_gain": r_gain,
        "d2_cutoff_after_r": cutoff_after_r,
        "r_tightened": cutoff_after_r < cutoff, "c_after_r": c_after_r, "c_close": c_close,
        "vp_owned": vp_owned,
        "vp_window": vp_window, "duplicate_credit": vp_window + r_gain - (c_open - c_close),
        "native_scores": native_scores, "eager_scores": eager_scores,
        "eager_witness_rows": witness_rows, "point_total_scores": point.n_scores,
        "point_total_probes": point.n_probes, "r_total_scores": relational.n_scores,
        "r_total_probes": relational.n_probes, "r_total_batches": relational.n_batches,
        "r_total_batch_ids": relational.n_batch_ids,
    }


def summarize(rows):
    pending = [row for row in rows if row["pending"] > 0]
    zero_score = [row for row in pending if row["c_open"] == row["c_after_score"]]
    crossover = [row for row in pending if row["r_direct"] > 0]
    r_closes = [row for row in crossover
                if row["pending"] == row["r_direct"] + row["r_threshold_retired"]]
    example = next((row for row in zero_score
                    if row in r_closes and row["point_drain_tightened"]), None)

    def scores_against(key):
        return {"fewer": sum(row["eager_scores"] < row[key] for row in rows),
                "equal": sum(row["eager_scores"] == row[key] for row in rows),
                "more": sum(row["eager_scores"] > row[key] for row in rows)}

    return {
        "queries": len(rows), "all_four_plans_match_oracle": len(rows),
        "short_result_queries": sum(not row["full_heap"] for row in rows),
        "no_pending_after_first_cohort": len(rows) - len(pending),
        "pending_after_first_cohort": len(pending),
        "pending_after_zero_gain_score": len(zero_score),
        "zero_gain_score_then_first_point_tightened": sum(
            row["point_first_tightened"] for row in zero_score),
        "zero_gain_score_then_draining_points_tightened": sum(
            row["point_drain_tightened"] for row in zero_score),
        "first_point_tightened": sum(row["point_first_tightened"] for row in rows),
        "r_directly_settled_some_pending": len(crossover),
        "r_directly_settled_no_pending_with_a_pending_cohort": len(pending) - len(crossover),
        "r_settled_or_retired_all_pending": len(r_closes),
        "positive_overcredit": sum(row["duplicate_credit"] > 0 for row in rows),
        "duplicate_credit_sum": sum(row["duplicate_credit"] for row in rows),
        "actual_reduction_sum": sum(row["c_open"] - row["c_close"] for row in rows),
        "pending_ids_sum": sum(row["pending"] for row in rows),
        "r_directly_settled_ids_sum": sum(row["r_direct"] for row in rows),
        "median_eager_witness_rows": statistics.median(row["eager_witness_rows"] for row in rows),
        "median_eager_scores": statistics.median(row["eager_scores"] for row in rows),
        "median_point_first_scores": statistics.median(row["point_total_scores"] for row in rows),
        "median_batch_interleaved_scores": statistics.median(row["r_total_scores"] for row in rows),
        "eager_score_comparison_point_first": scores_against("point_total_scores"),
        "eager_score_comparison_batch_interleaved": scores_against("r_total_scores"),
        "first_zero_gain_then_point_drain_tightened_and_r_closed": example,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="Directory containing u.item, u.user, u.data")
    parser.add_argument("--details-out", type=Path, help="Write per-query operation counts as CSV")
    args = parser.parse_args()
    profiles, reviewers, ratings, hashes = load_source(args.data_dir)
    occupations = sorted(set(reviewers.values()))
    eligible = {occupation: set() for occupation in occupations}
    for movie_id, user_id, stars in ratings:
        if stars == 5:
            eligible[reviewers[user_id]].add(movie_id)

    with closing(sqlite3.connect(":memory:")) as db:
        sql = Sql(db, profiles, reviewers, ratings)
        rows = [run_query(sql, profiles, eligible, seed, occupation)
                for seed in SEEDS for occupation in occupations]
        explain_params = {"seed": 1, "profile": 0, "occupation": occupations[0], "k": K}
        output = {
            "sqlite": sqlite3.sqlite_version, "sha256": hashes,
            "seed_ids": list(SEEDS), "occupations": occupations, "top_k": K,
            "correlated_exists_query_plan": [row[3] for row in db.execute(
                "EXPLAIN QUERY PLAN " + NATIVE, explain_params)],
            "prefilter_query_plan": [row[3] for row in db.execute(
                "EXPLAIN QUERY PLAN " + PREFILTER, explain_params)],
            **summarize(rows),
        }
    if args.details_out:
        with args.details_out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
