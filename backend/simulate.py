"""Reproducible Bernoulli bandit study; all reported numbers are computed here."""
from __future__ import annotations
import json
import platform
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / 'data'
WIDE = np.array([.10,.15,.20,.25,.30,.35,.40,.45,.50,.70])
CLOSE = np.array([.40,.41,.42,.43,.44,.45,.46,.47,.48,.50])

def random_argmax(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    tied = values == values.max(axis=1, keepdims=True)
    return np.argmax(np.where(tied, rng.random(values.shape), -1.0), axis=1)

def choose(q: np.ndarray, counts: np.ndarray, t: int, policy: dict,
           rng: np.random.Generator) -> np.ndarray:
    n, k = q.shape
    if t <= k:
        return np.full(n, t-1, dtype=int)
    if policy['kind'] == 'random':
        return rng.integers(k, size=n)
    if policy['kind'] == 'ucb':
        return random_argmax(q + policy['c'] * np.sqrt(np.log(t)/counts), rng)
    epsilon = policy.get('epsilon', 0.0)
    if policy['kind'] == 'decay':
        epsilon = min(1., 1/np.sqrt(t))
    greedy = random_argmax(q, rng)
    explore = rng.random(n) < epsilon
    return np.where(explore, rng.integers(k, size=n), greedy)

def update(q: np.ndarray, counts: np.ndarray, actions: np.ndarray,
           rewards: np.ndarray, alpha: float | None = None) -> None:
    rows = np.arange(q.shape[0])
    counts[rows, actions] += 1
    rate = 1/counts[rows, actions] if alpha is None else alpha
    q[rows, actions] += rate * (rewards-q[rows, actions])

def ci(x: np.ndarray) -> dict:
    return {'mean': float(x.mean()), 'half95': float(1.96*x.std(ddof=1)/np.sqrt(len(x)))}

def experiment(means: np.ndarray, policies: list[dict], n: int, horizon: int,
               seed: int, change: bool = False) -> dict:
    k = len(means)
    env = np.random.default_rng(np.random.SeedSequence([seed,0]))
    rows = np.arange(n)
    states = []
    for i,p in enumerate(policies):
        states.append(dict(p=p, rng=np.random.default_rng(np.random.SeedSequence([seed,i+1])),
            q=np.zeros((n,k)), counts=np.zeros((n,k),dtype=np.int64),
            rewards=np.zeros(n), regret=np.zeros(n), optimal=np.zeros(n),
            block_r=np.zeros(n), block_o=np.zeros(n), tail_o=np.zeros(n),
            curve=[], post_regret=np.zeros(n)))
    for t in range(1,horizon+1):
        mu = means[::-1] if change and t>horizon//2 else means
        # Shared potential outcomes at each (run, time, arm); policies see selected arm only.
        potential = env.random((n,k)) < mu
        best = mu.max()
        for s in states:
            a=choose(s['q'],s['counts'],t,s['p'],s['rng'])
            r=potential[rows,a].astype(float)
            loss=best-mu[a]
            opt=(mu[a]==best).astype(float)
            update(s['q'],s['counts'],a,r,s['p'].get('alpha'))
            s['rewards']+=r; s['regret']+=loss; s['optimal']+=opt
            s['block_r']+=r; s['block_o']+=opt
            if t>horizon-1000: s['tail_o']+=opt
            if t>horizon//2: s['post_regret']+=loss
            if t%100==0:
                s['curve'].append(dict(t=t, regret=ci(s['regret']),
                    reward=ci(s['block_r']/100), optimal=ci(s['block_o']/100)))
                s['block_r'].fill(0);s['block_o'].fill(0)
    result={}
    for s in states:
        assert np.all(s['counts'].sum(axis=1)==horizon)
        assert np.all(np.isfinite(s['q'])) and np.all((s['q']>=0)&(s['q']<=1))
        result[s['p']['name']] = dict(policy=s['p'], reward=ci(s['rewards']/horizon),
            total_reward=ci(s['rewards']), regret=ci(s['regret']),
            optimal=ci(s['optimal']/horizon*100), tail_optimal=ci(s['tail_o']/min(1000,horizon)*100),
            post_regret=ci(s['post_regret']), pulls=s['counts'].mean(axis=0).tolist(),
            curve=s['curve'], run_regrets=s['regret'].tolist())
    if 'Epsilon 0.10' in result and 'UCB1' in result:
        difference=np.array(result['UCB1']['run_regrets'])-np.array(result['Epsilon 0.10']['run_regrets'])
        result['_paired_ucb_minus_epsilon']=ci(difference)
    return result

def main() -> None:
    start=time.monotonic()
    policies=[{'name':'Uniform random','kind':'random'},
        {'name':'Greedy','kind':'epsilon','epsilon':0.},
        {'name':'Epsilon 0.10','kind':'epsilon','epsilon':.1},
        {'name':'UCB1','kind':'ucb','c':float(np.sqrt(2))}]
    out={'metadata':dict(n=500,horizon=10000,k=10,seed=20261111,
        numpy=np.__version__,python=platform.python_version(),
        stationary_wide=WIDE.tolist(),stationary_close=CLOSE.tolist(),
        switch_round=5001,sensitivity_n=300,sensitivity_horizon=5000)}
    for j,(name,means,change) in enumerate([('wide',WIDE,False),('close',CLOSE,False),('switch',WIDE,True)]):
        ps=policies.copy()
        if change: ps=ps+[{'name':'Epsilon alpha 0.10','kind':'epsilon','epsilon':.1,'alpha':.1}]
        out[name]=experiment(means,ps,500,10000,20261111+j,change)
        print(name,{p['name']:round(out[name][p['name']]['regret']['mean'],2) for p in ps},flush=True)
    sensitivity=[{'name':f'eps={e:.2f}','kind':'epsilon','epsilon':e} for e in [.01,.05,.1,.2]]
    sensitivity += [{'name':'decay','kind':'decay'}]
    sensitivity += [{'name':f'c={c:.3f}','kind':'ucb','c':c} for c in [.25,.5,1.,float(np.sqrt(2)),2.]]
    for j,(name,means) in enumerate([('wide',WIDE),('close',CLOSE)]):
        out['sensitivity_'+name]=experiment(means,sensitivity,300,5000,20262111+j)
        print('sensitivity',name,'complete',flush=True)
    out['metadata']['elapsed_seconds']=time.monotonic()-start
    (ROOT/'results.json').write_text(json.dumps(out,indent=2))
    print('Results saved',round(out['metadata']['elapsed_seconds'],1),'seconds',flush=True)

if __name__=='__main__': main()
