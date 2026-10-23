"""Section 4.1: dependent work and the explicit unit-16 refresh."""
import json
from pathlib import Path

def run(policy):
    # Incumbent is already eligible at distance 10. Block A has one positive
    # at distance 1 and 63 negative documents at distance 5; its bound is zero.
    # Block B has 1000 negative documents at distance 4 and bound two.
    # Vector storage exposes all of A in one unit. The relational iterator's
    # fixed order sees A's negatives before its positive, one per work unit.
    e=[None]*1064; scored=set(); tau=10; elapsed=0; trace=[]
    distance=[1]+[5]*63+[4]*1000
    # Admissible learned statistics from an earlier execution prefix:
    # V had zero direct removals; P had eight. R removed one per time unit.
    gain={'V':0.0,'P':8.0,'R':1.0}; duration={a:1.0 for a in gain}
    joint_g=8.0; joint_t=2.0
    def count():
        return sum(v is None and ((distance[i]<=tau) if i in scored else ((0 if i<64 else 2)<=tau)) for i,v in enumerate(e))
    while count():
        ready=['R']+(['V'] if len(scored)<1064 else [])+(['P'] if 0 in scored and e[0] is None else [])
        if policy=='split' and elapsed==16 and 'V' in ready:
            action='V' # the explicit stale-class refresh rescues the producer
        else:
            def rate(a):
                return joint_g/joint_t if policy=='pooled' and a in ('V','P') else gain[a]/duration[a]
            action=max(ready,key=lambda a:(rate(a),a=='P'))
        before=count()
        if action=='V':
            next_ids=[i for i in range(1064) if i not in scored][:64]
            scored.update(next_ids)
        elif action=='P':e[0]=True;tau=1
        else:
            negative=next((i for i in range(1,64) if e[i] is None),None)
            if negative is None:e[0]=True;scored.add(0);tau=1
            else:e[negative]=False
        g=before-count();assert g>=0
        gain[action]=.75*gain[action]+.25*g
        duration[action]=.75*duration[action]+.25
        if action in ('V','P'):
            joint_g=.75*joint_g+.25*g
            joint_t=.75*joint_t+.25
        trace.append({'action':action,'gain':g,'remaining':count()})
        elapsed+=1
        assert elapsed<100
    assert e[0] is True and tau==1
    assert sum(x['gain'] for x in trace)==1064
    return {'time_units':elapsed,'trace':trace,'exact_best_distance':tau}

