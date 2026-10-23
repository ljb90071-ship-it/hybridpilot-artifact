"""Executable completion-stage reference using exact integer distances.
The fixed k=1 incumbent is (10,-1). Blocks contain four IDs; VP cohorts two.
Each witness advance has a rational work cost. This isolates the retained
state, single pinned probe, episode ownership and Algorithm 1 dispatch.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
import random, json, re

def ewma(old, gain, time):
    return ((3*old[0]+gain)/4, (3*old[1]+time)/4)

def run(seed, mode, instance=None, detail=False):
    rng=random.Random(seed)
    n=rng.randrange(8,41)
    d=[rng.randrange(0,21) for _ in range(n)]
    eligible=[rng.random()<.4 for _ in range(n)]
    fan=[rng.randrange(0,9) for _ in range(n)]
    eligible=[ok and f>0 for ok,f in zip(eligible,fan)]
    end=[rng.randint(1,f) if ok else max(1,f) for ok,f in zip(eligible,fan)]
    if instance is not None:
        d=instance['distances']; eligible=instance['eligible']; end=instance['witness_advances']
        n=len(d)
        if not (len(eligible)==len(end)==n and n>0):
            raise ValueError('Input lists must be nonempty and equally sized')
        if not all(type(x) is bool for x in eligible):
            raise ValueError('Eligibility values must be Boolean')
        if not all(type(x) is int and x>=0 for x in d):
            raise ValueError('Distances must be nonnegative integers')
        if not all(type(x) is int and x>=1 for x in end):
            raise ValueError('Witness advances must be positive integers')
    blocks=[list(range(i,min(i+4,n))) for i in range(0,n,4)]
    lo=[max(0,min(d[x] for x in b)-rng.randrange(4)) for b in blocks]
    order=sorted(range(len(blocks)),key=lambda j:(lo[j],j))
    cohorts=[b[i:i+2] for j in order for b in [blocks[j]] for i in range(0,len(b),2)]
    segments=[blocks[j] for j in order]
    block={x:j for j,b in enumerate(blocks) for x in b}
    scored=set(); qual={}; pcur=defaultdict(int); rcur=defaultdict(int)
    heap=[(10,-1)]; pinned=None
    vi=ri=0
    totals={'VP':[0,F(0)],'R':[0,F(0)]}
    completed=[]; events=[]; foreign=0; steps=0
    threshold_gain=0; direct_R=0
    cumulative={a:[F(12),F(3)] for a in ('VP','R')}
    history={a:(F(4),F(1)) for a in ('VP','R')}
    current='R'
    def tau():return heap[0][0]
    def pending():return {x for x in scored if x not in qual and d[x]<=tau()}
    def relevant(x):
        return x not in qual and (d[x] if x in scored else lo[block[x]])<=tau()
    def count_at(limit):
        return sum(x not in qual and ((d[x] if x in scored else lo[block[x]])<=limit) for x in range(n))
    def count():
        q=pending()
        u=[sum(x not in qual and x not in scored for x in b) for b in blocks]
        assert not (q & {x for x in range(n) if x not in qual and x not in scored})
        assert len(q)<=2
        return len(q)+sum(u[j] for j in range(len(blocks)) if lo[j]<=tau())
    def commit(x):
        nonlocal heap
        qual[x]=eligible[x]
        if eligible[x]:
            scored.add(x)
            heap=sorted(heap+[(d[x],x)])[:1]
    def close(lane):
        if totals[lane][1]:
            completed.append((lane,*totals[lane]))
            history[lane]=ewma(history[lane],*totals[lane])
        totals[lane]=[0,F(0)]
    def normalize():
        nonlocal vi,ri,pinned
        if pinned is not None and not relevant(pinned):pinned=None
        while vi<len(cohorts) and not any(relevant(x) for x in cohorts[vi]):
            close('VP');vi+=1
        while ri<len(segments) and not any(relevant(x) for x in segments[ri]):
            close('R');ri+=1
    initial=count()
    while count()>0:
        normalize()
        ready=[]
        if vi<len(cohorts):ready.append('VP')
        if ri<len(segments):ready.append('R')
        assert ready
        lane=(ready[0] if mode=='vector' else ready[-1] if mode=='relational' else rng.choice(ready))
        if mode in ('hybrid','cumulative'):
            def rate(a):
                if mode=='cumulative':return cumulative[a][0]/cumulative[a][1]
                g,t=history[a];ag,at=totals[a]
                return ((3*g+ag)/(3*t+at)) if at else g/t
            lane=max(ready,key=lambda a:(rate(a),a==current,a=='R'))
        current=lane
        before=count(); old_tau=tau(); remaining_before=set(pending())
        state_before=(len(scored),len(qual),sum(pcur.values()),sum(rcur.values()))
        if lane=='VP':
            c=cohorts[vi]
            todo=[x for x in c if relevant(x) and x not in scored]
            if todo:
                x=todo[0];scored.add(x);cost=F(1,3);kind='V'
            else:
                if pinned is None:pinned=min((x for x in c if relevant(x)),key=lambda x:(d[x],x))
                x=pinned;pcur[x]+=1;cost=F(2,3);kind='P'
                if pcur[x]>=end[x]:commit(x);pinned=None
        else:
            x=next(x for x in segments[ri] if relevant(x))
            rcur[x]+=1;cost=F(1,2);kind='R'
            if rcur[x]>=end[x]:commit(x)
        after=count();gain=before-after
        at_old_tau=count_at(old_tau)
        assert before>=at_old_tau>=after
        threshold_gain+=at_old_tau-after
        cumulative[lane][0]+=gain;cumulative[lane][1]+=cost
        assert gain>=0
        state_after=(len(scored),len(qual),sum(pcur.values()),sum(rcur.values()))
        assert state_after>state_before, (state_before,state_after)
        totals[lane][0]+=gain;totals[lane][1]+=cost
        events.append((lane,kind,gain,cost,vi if lane=='VP' else ri))
        if lane=='R':
            foreign+=len(remaining_before-pending())
            direct_R+=sum(x in qual for x in remaining_before)
        assert sum(e[2] for e in events)==initial-after
        assert sum(e[1] for e in completed)+sum(v[0] for v in totals.values())==initial-after
        steps+=1
        assert steps<=n+2*sum(end)
    answer=min([(10,-1)]+[(d[x],x) for x in range(n) if eligible[x]])
    assert heap[0]==answer
    close('VP');close('R')
    # Regroup primitive events at the unchanged episode boundaries.
    groups=defaultdict(list)
    for lane,kind,g,t,ep in events:groups[(lane,ep)].append((F(g),t))
    histories={a:(F(4),F(1)) for a in ('VP','R')}
    replay={a:(F(4),F(1)) for a in ('VP','R')}
    for (lane,ep),parts in groups.items():
        g=sum(x[0] for x in parts);t=sum(x[1] for x in parts)
        histories[lane]=ewma(histories[lane],g,t)
        # Arbitrary extra yields subdivide each cost without moving commits.
        divided=[]
        for gain,time in parts:
            splits=rng.randint(1,7)
            divided.extend([(F(0),time/splits)]*(splits-1))
            divided.append((gain,time/splits))
        replay[lane]=ewma(replay[lane],sum(x[0] for x in divided),sum(x[1] for x in divided))
    assert replay==histories
    assert history==histories
    for lane in ('VP','R'):
        assert cumulative[lane]==[F(12)+sum(e[2] for e in events if e[0]==lane),F(3)+sum(e[3] for e in events if e[0]==lane)]
    if detail:
        return {'seed':seed,'policy':mode,'initial_count':initial,'answer':heap[0],
                'exhaustive_answer':answer,'primitive_steps':steps,'R_resolved_pending':foreign,
                'R_direct_qualified_pending':direct_R,'threshold_retirements':threshold_gain,
                'threshold_fraction':threshold_gain/initial if initial else 0,
                'events':[{'lane':a,'operation':b,'gain':g,'cost_units':str(t),'episode':e}
                          for a,b,g,t,e in events],
                'closed_episodes':[{'lane':a,'gain':g,'cost_units':str(t)} for a,g,t in completed],
                'history':{a:[str(v) for v in h] for a,h in history.items()}}
    return steps,foreign,len(events)

def boundary_tests():
    old=(F(4),F(1))
    merged=ewma(old,F(8),F(2))
    split=ewma(ewma(old,F(0),F(1)),F(8),F(1))
    assert merged[0]/merged[1]==4
    assert split[0]/split[1]==F(17,4)
    assert 4<F(41,10)<F(17,4)
    # A producer's own zero-gain cost survives an R-induced cancellation.
    producer=ewma(old,F(0),F(2))
    assert producer==(F(3),F(5,4))
    assert producer[0]/producer[1]<old[0]/old[1]
    # No reward transfer: global C 10 -> 10 (V) -> 2 (R).
    assert (10-10)+(10-2)==8
    assert (10-2)+(10-2)==16 # deliberately wrong endpoint accounting
    # Conditional residual lifetime: mean-minus-sunk underestimates survivors.
    times=[1]*9+[10]
    unconditional=F(sum(times),len(times))
    survivors=[t for t in times if t>2]
    residual=F(sum(t-2 for t in survivors),len(survivors))
    assert residual==8 and max(F(1),unconditional-2)==1
    # Positive must drain before Complete can classify the remaining IDs.
    unknown={1,2};buffer=[1];positive=set()
    assert buffer and unknown
    for x in buffer:positive.add(x);unknown.remove(x)
    buffer.clear();negative=set(unknown)
    assert positive=={1} and negative=={2}
    # Equal distance cannot be retired merely on equality with the threshold.
    assert sorted([(3,8),(3,2)])[:1]==[(3,2)]
    return {'batch_rate_merged':4,'batch_rate_split':4.25,'survival_remaining':8}

