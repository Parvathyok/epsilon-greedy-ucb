"""Local comparison dashboard. Run with python -m backend.server."""
from __future__ import annotations
import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import mimetypes
import os
from pathlib import Path
from string import Template
from threading import BoundedSemaphore
from urllib.parse import parse_qs, urlparse
import numpy as np
from backend.simulate import experiment, WIDE, CLOSE

ROOT=Path(__file__).resolve().parents[1]
SCENARIOS={'wide':'Well-separated rewards','close':'Closely matched rewards','switch':'Reversal of the best action'}
SLOT=BoundedSemaphore(1)
STUDY=json.loads((ROOT/'data/results.json').read_text())

def value(form: dict[str,list[str]], key: str, default: str) -> str:
    return form.get(key,[default])[0]

def validate(form: dict[str,list[str]]) -> dict:
    scenario=value(form,'scenario','wide')
    if scenario not in SCENARIOS: raise ValueError('Choose one of the three reward scenarios.')
    try:
        runs=int(value(form,'runs','100')); horizon=int(value(form,'horizon','5000'))
        seed=int(value(form,'seed','42'));epsilon=float(value(form,'epsilon','0.1'));c=float(value(form,'c',str(math.sqrt(2))))
    except (ValueError,OverflowError) as err: raise ValueError('Enter valid numbers for all experiment settings.') from err
    if not 20<=runs<=500:raise ValueError('Use between 20 and 500 independent runs.')
    if not 100<=horizon<=10000 or horizon%100:raise ValueError('Use a horizon from 100 to 10,000 in steps of 100.')
    if not 0<=seed<=2**32-1:raise ValueError('Use an integer seed from 0 to 4,294,967,295.')
    if not math.isfinite(epsilon) or not 0<=epsilon<=1:raise ValueError('Exploration probability must be between 0 and 1.')
    if not math.isfinite(c) or not .05<=c<=3:raise ValueError('The UCB coefficient must be between 0.05 and 3.')
    return dict(scenario=scenario,runs=runs,horizon=horizon,seed=seed,epsilon=epsilon,c=c)

def custom_run(cfg: dict) -> dict:
    policies=[{'name':'Uniform random','kind':'random'}, {'name':'Greedy','kind':'epsilon','epsilon':0.},
        {'name':f"Epsilon {cfg['epsilon']:.2f}",'kind':'epsilon','epsilon':cfg['epsilon']},
        {'name':'UCB1' if abs(cfg['c']-math.sqrt(2))<1e-10 else f"UCB c={cfg['c']:g}",'kind':'ucb','c':cfg['c']}]
    means=CLOSE if cfg['scenario']=='close' else WIDE
    return experiment(means,policies,cfg['runs'],cfg['horizon'],cfg['seed'],cfg['scenario']=='switch')

def chart(data: dict,horizon: int) -> str:
    chosen=[(name,v) for name,v in data.items() if not name.startswith('_') and v['policy']['kind'] in ('epsilon','ucb') and name!='Greedy']
    width,height=760,300;left,right,top,bottom=56,20,20,42
    w=width-left-right;h=height-top-bottom
    ceiling=max([v['curve'][-1]['regret']['mean']+v['curve'][-1]['regret']['half95'] for _,v in chosen]+[1])*1.08
    def xy(x:float,y:float)->tuple[float,float]:return left+w*x/horizon,top+h*(1-y/ceiling)
    svg=[f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc"><title id="chart-title">Cumulative pseudo-regret</title><desc id="chart-desc">Lower values mean less reward lost to action selection. Pointwise 95 percent intervals are shaded.</desc>']
    for i in range(5):
        v=ceiling*i/4;x,y=xy(0,v)
        svg.append(f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" stroke="#deddd7"/><text x="{left-10}" y="{y+4}" text-anchor="end">{v:,.0f}</text>')
    for t in [0,horizon//2,horizon]:
        x,y=xy(t,0);anchor='end' if t==horizon else 'middle'
        svg.append(f'<text x="{x}" y="{y+24}" text-anchor="{anchor}">{t:,}</text>')
    if horizon and len(data)>0:
        for i,(name,v) in enumerate(chosen):
            curve=v['curve']; points=' '.join(f'{x:.2f},{y:.2f}' for x,y in [xy(z['t'],z['regret']['mean']) for z in curve])
            band=[xy(z['t'],z['regret']['mean']+z['regret']['half95']) for z in curve]+[xy(z['t'],max(0,z['regret']['mean']-z['regret']['half95'])) for z in reversed(curve)]
            is_ucb=v['policy']['kind']=='ucb';is_constant='alpha' in v['policy']
            shade='#ddd9d0' if is_ucb else '#b8b5ae';stroke='#171717' if is_ucb else ('#99958d' if is_constant else '#777269');dash='' if is_ucb else ('2 4' if is_constant else '8 5')
            polygon=' '.join(f'{x:.2f},{y:.2f}' for x,y in band)
            svg.append(f'<polygon points="{polygon}" fill="{shade}" fill-opacity="0.4"/><polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="2.5" stroke-dasharray="{dash}"/>')
    svg.append('</svg>')
    return ''.join(svg)

def render(data:dict,cfg:dict,saved:bool=True,error:str='')->bytes:
    options=''.join(f'<option value="{key}" {"selected" if key==cfg["scenario"] else ""}>{label}</option>' for key,label in SCENARIOS.items())
    rows=[];legend=[]
    for name,v in data.items():
        if name.startswith('_'):continue
        rows.append('<tr><th scope="row">'+escape(name.replace('Epsilon','ε-greedy'))+'</th>'+''.join(f'<td>{v[key]["mean"]:,.{digits}f}<span class="interval"> ± {v[key]["half95"]:,.{digits}f}</span></td>' for key,digits in [('reward',4),('regret',1)])+f'<td>{v["tail_optimal"]["mean"]:.1f}%</td></tr>')
        if v['policy']['kind'] in ('epsilon','ucb') and name!='Greedy':legend.append(escape(name.replace('Epsilon','ε-greedy')))
    descriptions={'wide':'One action has a clear advantage: its reward probability is 0.70, compared with 0.50 for the next best.',
      'close':'The top two reward probabilities are 0.50 and 0.48. A small gap makes it harder to distinguish the actions.',
      'switch':f"Reward probabilities reverse after round {cfg['horizon']//2:,}. The learner receives no change notification."}
    template=Template((ROOT/'frontend/index.html').read_text())
    return template.substitute(title=SCENARIOS[cfg['scenario']],options=options,
        runs=cfg['runs'],horizon=cfg['horizon'],seed=cfg['seed'],epsilon=cfg['epsilon'],coefficient=f"{cfg['c']:.15g}",
        status='Saved report study' if saved else 'New comparison',description=descriptions[cfg['scenario']],
        chart=chart(data,cfg['horizon']),legend=' · '.join(legend),rows=''.join(rows),
        error=f'<p class="error" role="alert">{escape(error)}</p>' if error else '',
        note='These are the measured results used in the report.' if saved else 'This comparison is temporary. The report study and its saved data are unchanged.',
        tail=min(cfg['horizon'],1000)).encode()

class Handler(BaseHTTPRequestHandler):
    def send(self,body:bytes,status:int=200,content_type:str='text/html; charset=utf-8')->None:
        self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self)->None:
        url=urlparse(self.path)
        if url.path in ('/','/study'):
            scene=value(parse_qs(url.query),'scenario','wide')
            if scene not in SCENARIOS:scene='wide'
            cfg=dict(scenario=scene,runs=500,horizon=10000,seed=20261111+list(SCENARIOS).index(scene),epsilon=.1,c=math.sqrt(2))
            self.send(render(STUDY[scene],cfg));return
        if url.path=='/api/health':self.send(b'{"status":"ok"}',content_type='application/json');return
        if url.path=='/api/study':self.send(json.dumps(STUDY).encode(),content_type='application/json');return
        mapping={'/styles.css':ROOT/'frontend/styles.css','/results.csv':ROOT/'data/summary.csv',
          '/report.docx':ROOT/'reports/Parvathy_OK_Epsilon_Greedy_and_UCB_Report.docx',
          '/report.pdf':ROOT/'reports/Parvathy_OK_Epsilon_Greedy_and_UCB_Report.pdf'}
        file=mapping.get(url.path)
        if file and file.is_file():self.send(file.read_bytes(),content_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream');return
        self.send(b'Not found',404,'text/plain')
    def do_POST(self)->None:
        if self.path!='/simulate':self.send(b'Not found',404,'text/plain');return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>4096:raise ValueError('The request is too large or empty.')
            cfg=validate(parse_qs(self.rfile.read(length).decode()))
            if not SLOT.acquire(blocking=False):raise ValueError('Another comparison is running. Try again in a moment.')
            try:result=custom_run(cfg)
            finally:SLOT.release()
            self.send(render(result,cfg,False))
        except (ValueError,UnicodeDecodeError) as err:
            cfg=dict(scenario='wide',runs=500,horizon=10000,seed=20261111,epsilon=.1,c=math.sqrt(2))
            self.send(render(STUDY['wide'],cfg,True,str(err)),400)

def main()->None:
    parser=argparse.ArgumentParser(description='Open the local bandit comparison dashboard.')
    parser.add_argument('--port',type=int,default=int(os.environ.get('PORT','8000')))
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Bandit comparison: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
