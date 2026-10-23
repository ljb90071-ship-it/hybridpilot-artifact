# Archived result tables

Generated from the supplied CSV files; times and aggregation are defined in results/README.md.

## workloads.csv

| family | documents | dimensions | relations | fanout_median | fanout_p99 | radius | entry_Q_over_u | threshold_removals_pct | relevant_blocks_envelope_upper_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Catalog | 10000000 | 384 | 4 | 8 | 420 | 0.45 | 0 | 44 | 0.634765625 |
| Documents | 8000000 | 768 | 5 | 4 | 180 | 0.75 | 0 | 31 | 1.5625 |
| Media | 12000000 | 512 | 4 | 12 | 910 | 1 | 0 | 49 | 1.5625 |

## latency.csv

| policy | family | queries | geomean_ms | p95_ms |
| --- | --- | --- | --- | --- |
| SplitRate | Catalog | 600 | 78 | 358 |
| SplitRate | Documents | 600 | 105 | 452 |
| SplitRate | Media | 600 | 149 | 691 |
| Yield episodes | Catalog | 600 | 70 | 309 |
| Yield episodes | Documents | 600 | 96 | 407 |
| Yield episodes | Media | 600 | 132 | 582 |
| Work episodes | Catalog | 600 | 67 | 291 |
| Work episodes | Documents | 600 | 91 | 378 |
| Work episodes | Media | 600 | 126 | 539 |
| AutoCost | Catalog | 600 | 64 | 271 |
| AutoCost | Documents | 600 | 88 | 352 |
| AutoCost | Media | 600 | 122 | 487 |
| RankBenefit | Catalog | 600 | 62 | 260 |
| RankBenefit | Documents | 600 | 85 | 339 |
| RankBenefit | Media | 600 | 116 | 465 |
| HybridPilot | Catalog | 600 | 57 | 236 |
| HybridPilot | Documents | 600 | 80 | 327 |
| HybridPilot | Media | 600 | 106 | 431 |

## regimes.csv

| group | queries | AutoCost_ms | RankBenefit_ms | HybridPilot_ms |
| --- | --- | --- | --- | --- |
| Dependent near probes | 60 | 151 | 139 | 121 |
| Threshold leverage | 60 | 103 | 95 | 84 |
| Weak bounds | 60 | 86 | 90 | 92 |
| Shared preparation | 60 | 142 | 148 | 153 |
| Cheap membership | 60 | 27 | 30 | 30 |

## accounting.csv

| grouping | update | queries | geomean_ms |
| --- | --- | --- | --- |
| separate | physical | 120 | 139 |
| separate | logical | 120 | 132 |
| joint | physical | 120 | 115 |
| joint | logical | 120 | 106 |

## slices.csv

| budget_ms | physical_geomean_ms | logical_geomean_ms | queries |
| --- | --- | --- | --- |
| 0.25 | 124 | 112 | 120 |
| 1 | 115 | 106 | 120 |
| 4 | 129 | 116 | 120 |

## simple_controls.csv

| policy | family | queries | geomean_ms |
| --- | --- | --- | --- |
| VP-only | Catalog | 600 | 73 |
| VP-only | Documents | 600 | 111 |
| VP-only | Media | 600 | 140 |
| R-only | Catalog | 600 | 89 |
| R-only | Documents | 600 | 99 |
| R-only | Media | 600 | 159 |
| OnceCost | Catalog | 600 | 68 |
| OnceCost | Documents | 600 | 94 |
| OnceCost | Media | 600 | 129 |
| Cumulative | Catalog | 600 | 59 |
| Cumulative | Documents | 600 | 83 |
| Cumulative | Media | 600 | 111 |
| HybridPilot | Catalog | 600 | 57 |
| HybridPilot | Documents | 600 | 80 |
| HybridPilot | Media | 600 | 106 |

AutoCost / HybridPilot geometric-mean ratios: 1.12, 1.10, 1.15.
