"""Export the completed study to portable, full-precision CSV tables."""
from pathlib import Path
import csv,json

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/results.json').read_text())
with (ROOT/'data/summary.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['scenario','policy','mean_reward','reward_ci95_half','mean_regret','regret_ci95_half','optimal_pct','last_1000_optimal_pct'])
    for scene,policies in data.items():
        if scene=='metadata':continue
        for name,v in policies.items():
            if name.startswith('_'):continue
            writer.writerow([scene,name,v['reward']['mean'],v['reward']['half95'],v['regret']['mean'],v['regret']['half95'],v['optimal']['mean'],v['tail_optimal']['mean']])
with (ROOT/'data/learning_curves.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['scenario','policy','round','regret_mean','regret_ci95_half','block_reward_mean','block_reward_ci95_half','block_optimal_fraction'])
    for scene,policies in data.items():
        if scene=='metadata':continue
        for name,v in policies.items():
            if name.startswith('_'):continue
            for x in v['curve']:writer.writerow([scene,name,x['t'],x['regret']['mean'],x['regret']['half95'],x['reward']['mean'],x['reward']['half95'],x['optimal']['mean']])
with (ROOT/'data/run_regrets.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['scenario','policy','run','pseudo_regret'])
    for scene,policies in data.items():
        if scene=='metadata':continue
        for name,v in policies.items():
            if name.startswith('_'):continue
            for i,v in enumerate(v['run_regrets'],1):writer.writerow([scene,name,i,v])
print('Exported summary.csv, learning_curves.csv and run_regrets.csv')
