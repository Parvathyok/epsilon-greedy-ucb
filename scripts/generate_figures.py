"""Print-ready vector diagrams and measured-data charts, rasterized at 300 dpi."""
from pathlib import Path
import json, math
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from pdf2image import convert_from_path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report_assets'/'figures';OUT.mkdir(exist_ok=True)
R=json.loads((ROOT/'data'/'results.json').read_text())
import os
POPPLER=os.environ.get('POPPLER_PATH')

def start(name,w=504,h=250):
    c=canvas.Canvas(str(OUT/f'{name}.pdf'),pagesize=(w,h));c.setTitle(name.replace('_',' '));return c
def finish(c,name):
    c.save();convert_from_path(str(OUT/f'{name}.pdf'),dpi=300,poppler_path=POPPLER)[0].save(OUT/f'{name}.png')
def text(c,x,y,s,size=10,bold=False,align='left'):
    c.setFillColorRGB(0,0,0);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
    getattr(c,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x,y,s)
def box(c,x,y,w,h,lines,fill=.965):
    c.setFillColor(Color(fill,fill,fill));c.setStrokeColorRGB(.15,.15,.15);c.setLineWidth(.8)
    c.roundRect(x,y,w,h,4,fill=1,stroke=1)
    for i,s in enumerate(lines):text(c,x+w/2,y+h/2+(len(lines)-1)*7-i*14,s,10,i==0,'center')
def arrow(c,x1,y1,x2,y2,label=None):
    c.setStrokeColorRGB(.2,.2,.2);c.setFillColorRGB(.2,.2,.2);c.setLineWidth(.9);c.setDash()
    c.line(x1,y1,x2,y2);a=math.atan2(y2-y1,x2-x1)
    p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-6*math.cos(a-.4),y2-6*math.sin(a-.4));p.lineTo(x2-6*math.cos(a+.4),y2-6*math.sin(a+.4));p.close();c.drawPath(p,fill=1,stroke=0)
    if label:
        xx=(x1+x2)/2;yy=(y1+y2)/2+5
        ww=c.stringWidth(label,'Helvetica',9)
        c.setFillColorRGB(1,1,1);c.rect(xx-ww/2-3,yy-2,ww+6,12,fill=1,stroke=0)
        text(c,xx,yy,label,9,False,'center')

def loop():
    c=start('decision_loop',504,230)
    box(c,8,100,144,73,['Action selector','Uses past observations'])
    box(c,352,100,144,73,['Bandit environment','10 unknown reward rates'])
    box(c,180,12,144,53,['Update estimates','Counts and mean rewards'])
    arrow(c,152,151,352,151,'Choose one action')
    text(c,252,119,'Unchosen rewards remain hidden.',9,False,'center')
    arrow(c,424,100,324,38,'Reward');arrow(c,180,38,80,100,'New estimates')
    text(c,252,207,'LEARN THROUGH REPEATED ACTIONS',11,True,'center')
    finish(c,'decision_loop')

def architecture():
    c=start('experiment_pipeline',504,250)
    box(c,151,193,202,45,['Experiment configuration','Means, horizon and seed'])
    box(c,8,102,144,53,['Potential reward generator','Shared across policies'])
    box(c,180,102,144,53,['Policy runner','One action per round'])
    box(c,352,102,144,53,['Evaluation only','True means and regret'])
    box(c,151,12,202,49,['Aggregated results','Tables, intervals and figures'])
    arrow(c,183,193,80,155);arrow(c,252,193,252,155);arrow(c,321,193,424,155)
    arrow(c,152,129,180,129);arrow(c,324,129,352,129)
    arrow(c,252,102,252,61);arrow(c,424,102,325,61)
    text(c,80,83,'Selected reward only',8.5,False,'center')
    text(c,424,83,'No policy access',8.5,False,'center')
    finish(c,'experiment_pipeline')

def flows():
    c=start('policy_flowcharts',504,337)
    text(c,123,321,'EPSILON-GREEDY',12,True,'center');text(c,381,321,'UCB1',12,True,'center')
    for x in [13,271]:box(c,x,259,220,42,['Initialize','Pull each arm once'])
    box(c,13,189,220,43,['Draw a random number u','Uniformly between 0 and 1'])
    box(c,13,108,103,51,['u < epsilon','Uniform action'])
    box(c,130,108,103,51,['Otherwise','Largest mean'])
    box(c,271,189,220,43,['Compute each index','Mean + uncertainty bonus'])
    box(c,271,108,220,51,['Select the largest index','Break equal scores randomly'])
    for x in [13,271]:
        box(c,x,24,220,49,['Observe reward and update','Repeat until the horizon ends'])
        arrow(c,x+110,259,x+110,232)
    arrow(c,65,189,65,159);arrow(c,182,189,182,159)
    arrow(c,65,108,65,73);arrow(c,182,108,182,73)
    arrow(c,381,189,381,159);arrow(c,381,108,381,73)
    text(c,252,3,'Both methods use identical initialization and sample-mean updates.',8.8,False,'center')
    finish(c,'policy_flowcharts')

def axes(c,x,y,w,h,xmin,xmax,ymin,ymax,xticks,yticks,xlabel,ylabel,title):
    text(c,x,y+h+29,title,10.5,True)
    text(c,x,y+h+13,ylabel,9)
    c.setLineWidth(.45);c.setDash()
    for v in yticks:
        yy=y+(v-ymin)/(ymax-ymin)*h;c.setStrokeColorRGB(.85,.85,.85);c.line(x,yy,x+w,yy)
        label=f'{v:g}';text(c,x-7,yy-3,label,8.5,False,'right')
    for v,label in xticks:
        xx=x+(v-xmin)/(xmax-xmin)*w;text(c,xx,y-14,str(label),8.5,False,'right' if v==xmax else 'center')
    c.setStrokeColorRGB(.25,.25,.25);c.line(x,y,x+w,y);c.line(x,y,x,y+h)
    text(c,x+w/2,y-31,xlabel,9,False,'center')
    return lambda a,b:(x+(a-xmin)/(xmax-xmin)*w,y+(b-ymin)/(ymax-ymin)*h)

def series(c,mapxy,xs,ys,dash=(),gray=0,width=1.5,half=None):
    if half is not None:
        pts=[mapxy(x,y+h) for x,y,h in zip(xs,ys,half)]+[mapxy(x,y-h) for x,y,h in zip(xs[::-1],ys[::-1],half[::-1])]
        c.setFillColor(Color(.86 if gray else .93,.86 if gray else .93,.86 if gray else .93))
        p=c.beginPath();p.moveTo(*pts[0])
        for pt in pts[1:]:p.lineTo(*pt)
        p.close();c.drawPath(p,fill=1,stroke=0)
    c.setStrokeColorRGB(gray,gray,gray);c.setLineWidth(width);c.setDash(dash)
    p=c.beginPath();p.moveTo(*mapxy(xs[0],ys[0]))
    for x,y in zip(xs[1:],ys[1:]):p.lineTo(*mapxy(x,y))
    c.drawPath(p);c.setDash()
def legend(c,items,y=14):
    x=45
    for label,dash,gray in items:
        c.setLineWidth(1.6);c.setDash(dash);c.setStrokeColorRGB(gray,gray,gray);c.line(x,y+3,x+23,y+3);c.setDash()
        text(c,x+29,y,label,9);x+=len(label)*4.8+66

def performance(scenario):
    c=start(f'{scenario}_performance',504,260)
    wide=scenario=='wide';r=R[scenario]
    m1=axes(c,45,65,196,137,0,10000,0,450 if wide else 450,[(0,'0'),(5000,'5,000'),(10000,'10,000')],[0,100,200,300,400],'Round','Cumulative pseudo-regret','(a) Cost of action choices')
    m2=axes(c,300,65,191,137,0,10000,.3 if wide else .40,.72 if wide else .51,[(0,'0'),(5000,'5,000'),(10000,'10,000')],[.3,.4,.5,.6,.7] if wide else [.40,.43,.46,.49],'Round','Reward per round','(b) Learning progress')
    for name,dash,g in [('Epsilon 0.10',(5,3),.35),('UCB1',(),0)]:
        curve=r[name]['curve'];xs=[a['t'] for a in curve]
        for field,m in [('regret',m1),('reward',m2)]:
            series(c,m,xs,[a[field]['mean'] for a in curve],dash,g,half=[a[field]['half95'] for a in curve])
    series(c,m2,[0,10000],[.7 if wide else .5]*2,(1,3),.5,width=.7)
    legend(c,[('Epsilon = 0.10',(5,3),.35),('UCB1',(),0)],16)
    finish(c,f'{scenario}_performance')

def switching():
    c=start('switch_performance',504,270)
    m=axes(c,45,70,445,145,0,10000,0,100,[(0,'0'),(2500,'2,500'),(5000,'5,000'),(7500,'7,500'),(10000,'10,000')],[0,25,50,75,100],'Round','Best-action selection (%)','Response to the reversal of reward rates')
    x,y=m(5000,0);c.setDash(2,2);c.setStrokeColorRGB(.6,.6,.6);c.line(x,y,x,y+145);c.setDash()
    text(c,x+12,y+54,'Change at round 5,001',8.8)
    items=[('Epsilon 0.10',(5,3),.35),('UCB1',(),0),('Epsilon alpha 0.10',(1,3),.6)]
    for name,dash,g in items:
        curve=R['switch'][name]['curve']
        series(c,m,[a['t'] for a in curve],[a['optimal']['mean']*100 for a in curve],dash,g)
    legend(c,[('Sample-mean epsilon',(5,3),.35),('UCB1',(),0),('Constant-step epsilon',(1,3),.6)],16)
    finish(c,'switch_performance')

def sensitivity():
    c=start('parameter_sensitivity',504,275)
    a=axes(c,45,75,192,140,.01,.2,0,450,[(.01,'.01'),(.05,'.05'),(.1,'.10'),(.2,'.20')],[0,100,200,300,400],'Exploration probability epsilon','Pseudo-regret at 5,000 rounds','(a) Epsilon-greedy')
    b=axes(c,300,75,190,140,.25,2,0,550,[(.25,'.25'),(.5,'.50'),(1,'1'),(1.414,'1.41'),(2,'2')],[0,100,200,300,400,500],'Exploration coefficient c','Pseudo-regret at 5,000 rounds','(b) UCB index variants')
    for scene,dash,g in [('wide',(),0),('close',(5,3),.4)]:
        for xs,keys,m in [([.01,.05,.1,.2],[f'eps={e:.2f}' for e in [.01,.05,.1,.2]],a),([.25,.5,1,2**.5,2],[f'c={e:.3f}' for e in [.25,.5,1,2**.5,2]],b)]:
            ss=[R['sensitivity_'+scene][k]['regret'] for k in keys];ys=[v['mean'] for v in ss]
            series(c,m,xs,ys,dash,g)
            for x,v in zip(xs,ss):
                xx,lo=m(x,v['mean']-v['half95']);_,hi=m(x,v['mean']+v['half95'])
                c.setStrokeColorRGB(g,g,g);c.setLineWidth(.8);c.line(xx,lo,xx,hi);c.line(xx-3,lo,xx+3,lo);c.line(xx-3,hi,xx+3,hi)
                c.setFillColorRGB(g,g,g);c.circle(*m(x,v['mean']),2,fill=1,stroke=0)
    legend(c,[('Well-separated rewards',(),0),('Closely matched rewards',(5,3),.4)],18)
    finish(c,'parameter_sensitivity')

def allocation():
    c=start('arm_allocation',504,265)
    m=axes(c,45,67,445,144,.5,9.5,0,350,[(i,str(i)) for i in range(1,10)],[0,100,200,300],'Action number','Mean selections per run','Exploration of the nine suboptimal actions')
    for i in range(1,10):
        for offset,name,gray in [(-.17,'Epsilon 0.10',.7),(.17,'UCB1',.15)]:
            x,y=m(i+offset,0);_,top=m(i+offset,R['wide'][name]['pulls'][i-1]);c.setFillColorRGB(gray,gray,gray);c.rect(x-5,y,10,top-y,fill=1,stroke=0)
    for x,name,gray in [(80,'Epsilon = 0.10',.7),(260,'UCB1',.15)]:
        c.setFillColorRGB(gray,gray,gray);c.rect(x,16,12,8,fill=1,stroke=0);text(c,x+20,16,name,9)
    finish(c,'arm_allocation')

def reward_rates():
    c=start('reward_rates',504,245)
    m=axes(c,43,62,447,130,1,10,0,.8,[(i,str(i)) for i in range(1,11)],[0,.2,.4,.6,.8],'Action number','Probability of reward 1','Reward rates used in the simulations')
    for ys,dash,g in [(R['metadata']['stationary_wide'],(),0),(R['metadata']['stationary_close'],(5,3),.45)]:
        series(c,m,list(range(1,11)),ys,dash,g)
        for x,y in enumerate(ys,1):c.setFillColorRGB(g,g,g);c.circle(*m(x,y),2,fill=1,stroke=0)
    legend(c,[('Well-separated rewards',(),0),('Closely matched rewards',(5,3),.45)],12)
    finish(c,'reward_rates')

if __name__=='__main__':
    loop();architecture();flows();reward_rates();performance('wide');performance('close');switching();sensitivity();allocation()
    print('Created 9 vector figures and 300 dpi PNGs')
