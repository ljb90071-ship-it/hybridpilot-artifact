# MovieLens 100K exact-query replay

The replay uses MovieLens 100K from GroupLens. Obtain the data from the
[GroupLens dataset page](https://grouplens.org/datasets/movielens/100k/) and
follow its [usage terms](https://files.grouplens.org/datasets/movielens/ml-100k/README).
Use a local directory containing u.item, u.user, and u.data. Cite F. Maxwell
Harper and Joseph A. Konstan, *The MovieLens Datasets: History and Context*,
ACM TiiS, 2015, DOI [10.1145/2827872](https://doi.org/10.1145/2827872).

Python 3.10 or later with SQLite 3.35 or later suffices. From the supplement root:

~~~sh
python analysis/replay_movielens.py --data-dir PATH_TO_ML_100K --details-out movielens.csv > movielens.json
~~~

The script runs the cross product of seed film IDs 1–8 and the 21 occupations.
Ranking uses squared Euclidean distance on binary genre flags, then film ID.
Eligibility requires a five-star rating by a reviewer from the target occupation.
It verifies four exact SQL or saved-state continuations against independent
exhaustive ordering. The vector and point replay uses the same full-heap prefix
in both interleavings. The overlapping relation segment is chosen to include
the first scoring cohort's pending films. It demonstrates ownership in that
window and preserves the cost of the scores on the VP path.

The relational SQL comparison first selects reviewers by occupation, joins their
five-star ratings, deduplicates film IDs, and then scores them. A counting SQL
function records distance evaluations. The result includes SQLite's plan output,
local data hashes, aggregate counts, and one example query. See
[the reported output](../results/movielens_replay.json).

The [per-query table](../results/movielens_per_query.csv) lists operation and
attribution counts for each seed and occupation. Its rows aggregate the
execution of one query and use the same counters as the summary.
