"""Center-envelope diagnostic for the specified clustered workloads.
Computes conservative relevant-block bounds, not query latency or exact top-k.
The stream convention is SeedSequence([family_seed, salt, stream_id]).
"""
from pathlib import Path
import json
import numpy as np


def run(family, seed, n, radius, salt=0):
    geom = np.random.default_rng(np.random.SeedSequence([seed, salt, 10]))
    req = np.random.default_rng(np.random.SeedSequence([seed, salt, 20]))
    assign = np.random.default_rng(np.random.SeedSequence([seed, salt, 30]))
    macro = geom.normal(size=(64, 16))
    centers = (macro[:, None, :] + geom.normal(scale=.25, size=(64,64,16))).reshape(4096,16)
    max_center_norm = float(np.linalg.norm(centers,axis=1).max())
    # Componentwise IEEE float32 rounding gives ||fl(v)-v|| <= 2^-24||v||
    # for normal coordinates; subnormal absolute error is negligible here.
    # Four norm/radius terms safely cover vector, query, and center rounding.
    rounding_bound = 2**-24 * (4*max_center_norm + 4*radius)
    assert rounding_bound < 1e-4
    population = np.full(4096, n // 4096, dtype=np.int64)
    population[:n % 4096] += 1
    rates = [1e-4,1e-3,.01,.03,.1,.3]
    rows = []
    # Exactly 100 requests per selectivity, 200 per k, 300 per proximity mode.
    for ri, rate in enumerate(rates):
        ks = [10,50,100]
        kvals = [ks[j] for j in range(3) for _ in range(34 if j == ri % 3 else 33)]
        modes = ['uniform']*50 + ['near']*50
        req.shuffle(kvals); req.shuffle(modes)
        for k, mode in zip(kvals,modes):
            qi = int(req.integers(4096))
            direction = req.normal(size=16)
            direction /= np.linalg.norm(direction)
            q = centers[qi] + .3 * radius * direction
            dc = np.linalg.norm(centers-q, axis=1)
            m = round(n*rate)
            if mode == 'uniform':
                eligible = assign.multivariate_hypergeometric(population, m)
            else:
                macro_order = np.argsort(np.linalg.norm(macro-q, axis=1))
                near_target = round(.9*m)
                near_macros = []
                capacity = 0
                for mi in macro_order:
                    near_macros.append(int(mi))
                    capacity += int(population[mi*64:(mi+1)*64].sum())
                    if capacity >= near_target:
                        break
                mask = np.repeat(np.isin(np.arange(64), near_macros),64)
                eligible = np.zeros(4096,dtype=np.int64)
                eligible[mask] = assign.multivariate_hypergeometric(population[mask],near_target)
                eligible[~mask] = assign.multivariate_hypergeometric(population[~mask],m-near_target)
            ordered = np.argsort(dc)
            kth_block = ordered[np.searchsorted(np.cumsum(eligible[ordered]),k)]
            # 0.02r ambient noise and a small conservative rounding allowance.
            enclosing = 1.02*radius + 1e-4
            upper_tau = float(dc[kth_block] + enclosing)
            relevant_upper_count = int(np.count_nonzero(np.maximum(0,dc-enclosing)<=upper_tau))
            # Direction-independent variant: q is anywhere on/in a radius .3r
            # ball around the selected microcenter (including ambient directions).
            # ||c_j-q|| >= ||c_j-c_q||-.3r and <= ||c_j-c_q||+.3r.
            d0 = np.linalg.norm(centers-centers[qi],axis=1)
            ordered0 = np.argsort(d0)
            kth0 = ordered0[np.searchsorted(np.cumsum(eligible[ordered0]),k)]
            any_direction_tau = float(d0[kth0] + .3*radius + enclosing)
            any_direction_lower = np.maximum(0,d0-.3*radius-enclosing)
            any_direction_count = int(np.count_nonzero(any_direction_lower<=any_direction_tau))
            # Replacing every requested k by the maximum 100 only loosens the
            # threshold, removing sensitivity to this realization's k pairing.
            kth100 = ordered0[np.searchsorted(np.cumsum(eligible[ordered0]),100)]
            any_direction_k100_tau = float(d0[kth100] + .3*radius + enclosing)
            any_direction_k100_count = int(np.count_nonzero(any_direction_lower<=any_direction_k100_tau))
            rows.append({'selectivity':rate,'k':k,'mode':mode,'upper_tau':upper_tau,
                         'relevant_upper_count':relevant_upper_count,
                         'relevant_upper_pct':100*relevant_upper_count/4096,
                         'any_direction_upper_tau':any_direction_tau,
                         'any_direction_upper_count':any_direction_count,
                         'any_direction_upper_pct':100*any_direction_count/4096,
                         'any_direction_k100_upper_tau':any_direction_k100_tau,
                         'any_direction_k100_upper_count':any_direction_k100_count,
                         'any_direction_k100_upper_pct':100*any_direction_k100_count/4096})
    vals=np.array([x['relevant_upper_pct'] for x in rows])
    by_mode={m:float(np.median([x['relevant_upper_pct'] for x in rows if x['mode']==m])) for m in ['uniform','near']}
    return {'family':family,'seed':seed,'salt':salt,'queries':len(rows),
            'max_center_norm':max_center_norm,'rounding_bound':rounding_bound,
            'median_upper_pct':float(np.median(vals)),
            'p75_upper_pct':float(np.percentile(vals,75)),
            'max_upper_pct':float(vals.max()),'by_mode_median_upper_pct':by_mode,
            'at_most_64_blocks_queries':int(np.count_nonzero(vals<=100/64)),
            'any_direction_median_upper_pct':float(np.median([x['any_direction_upper_pct'] for x in rows])),
            'any_direction_at_most_64_blocks_queries':sum(x['any_direction_upper_count']<=64 for x in rows),
            'any_direction_k100_median_upper_pct':float(np.median([x['any_direction_k100_upper_pct'] for x in rows])),
            'any_direction_k100_at_most_64_blocks_queries':sum(x['any_direction_k100_upper_count']<=64 for x in rows),
            'rows':rows}


if __name__=='__main__':
    import argparse,csv
    p=argparse.ArgumentParser();p.add_argument('--output',default='geometry_bounds.csv');a=p.parse_args()
    records=[];summary=[]
    for args in [('Catalog',1101,10000000,.45),('Documents',1102,8000000,.75),('Media',1103,12000000,1.0)]:
        result=run(*args,salt=0)
        for i,row in enumerate(result['rows']):records.append({'family':args[0],'query_index':i,**row})
        summary.append({'family':args[0],'median_upper_pct':result['any_direction_k100_median_upper_pct']})
    with open(a.output,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
    print(json.dumps(summary,indent=2))
