from __future__ import annotations
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
from hashlib import sha256
import json, math
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT
REF=ROOT/'report_assets'/'report_template.docx'
OUT=BASE/'reports'/'Parvathy_OK_Epsilon_Greedy_and_UCB_Report.docx'
R=json.loads((ROOT/'data'/'results.json').read_text())
doc=Document(REF)
logo=deepcopy(doc.paragraphs[0]._p)
for el in list(doc._element.body):
    if el.tag!=qn('w:sectPr'):doc._element.body.remove(el)

# Preserve the source's page geometry and underlying style/theme definitions.
for s in doc.styles:
    if s.type in (1,2):
        s.font.color.rgb=RGBColor(0,0,0)
        for c in s.element.xpath('.//w:color'):
            for attr in ('themeColor','themeTint','themeShade'):
                c.attrib.pop(qn('w:'+attr),None)
            c.set(qn('w:val'),'000000')
normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.06
normal.paragraph_format.space_after=Pt(6)
normal.paragraph_format.widow_control=True
for name,size in [('Title',17),('Heading 1',14),('Heading 2',12),('Heading 3',11),('Caption',10)]:
    s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
    s.font.bold=name!='Caption';s.font.italic=name=='Caption'
    s.paragraph_format.space_before=Pt(12 if name.startswith('Heading') else 0)
    s.paragraph_format.space_after=Pt(6)
    s.paragraph_format.line_spacing=1.05
    s.paragraph_format.keep_with_next=name!='Caption'
    for b in s.element.xpath('.//w:pBdr'):b.getparent().remove(b)
for style_name in ['Normal','Title','Heading 1','Heading 2','Heading 3','Caption']:
    for fonts in doc.styles[style_name].element.xpath('.//w:rFonts'):
        for key in list(fonts.attrib):
            if 'theme' in key.lower():del fonts.attrib[key]
for sec in doc.sections:
    sec.different_first_page_header_footer=True
    sec.header_distance=Inches(.35);sec.footer_distance=Inches(.4)
    for hd in [sec.header,sec.first_page_header,sec.footer,sec.first_page_footer]:
        for p in hd.paragraphs:p.clear()
    p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run();r.font.size=Pt(9)
    f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE')
    rr=OxmlElement('w:r');tt=OxmlElement('w:t');tt.text='1';rr.append(tt);f.append(rr);p._p.append(f)
settings=doc.settings.element
for old in settings.findall(qn('w:updateFields')):settings.remove(old)
upd=OxmlElement('w:updateFields');upd.set(qn('w:val'),'true');settings.append(upd)
doc.core_properties.author='PARVATHY O K'
doc.core_properties.last_modified_by='PARVATHY O K'
doc.core_properties.title='Comparative Analysis of ε-Greedy and UCB Algorithms for Sequential Decision Making'
doc.core_properties.subject='Action Selection | 21CSE417TA Fundamentals of Reinforcement Learning'
doc.core_properties.keywords='multi-armed bandit, epsilon-greedy, UCB1, action selection, regret'
doc.core_properties.comments=''

def p(text='',bold=False,center=False,style=None):
    a=doc.add_paragraph(style=style);a.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    r=a.add_run(text);r.bold=bold
    return a
def h(text,level=2):return doc.add_paragraph(text,style=f'Heading {level}')
def page(title=None):
    if title:
        a=h(title,1);a.paragraph_format.space_before=Pt(0);a.paragraph_format.page_break_before=True
    else:doc.add_page_break()
def small(text):
    a=p(text)
    for r in a.runs:r.font.size=Pt(9.5)
    return a
def fig(name,caption,width=6.7):
    width=min(width,6.0)
    a=doc.add_paragraph();a.alignment=WD_ALIGN_PARAGRAPH.CENTER
    a.paragraph_format.space_before=Pt(4);a.paragraph_format.space_after=Pt(3);a.paragraph_format.keep_with_next=True
    r=a.add_run();r.add_picture(str(ROOT/'report_assets'/'figures'/f'{name}.png'),width=Inches(width))
    for pr in a._p.xpath('.//wp:docPr'):pr.set('descr',caption)
    a=doc.add_paragraph(caption,style='Caption');a.alignment=WD_ALIGN_PARAGRAPH.CENTER
    a.paragraph_format.space_after=Pt(9)
def table(headers,rows,widths,caption=None,size=10):
    if caption:
        a=doc.add_paragraph(caption,style='Caption');a.paragraph_format.keep_with_next=True;a.alignment=WD_ALIGN_PARAGRAPH.LEFT
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Inches(w)
    for i,v in enumerate(headers):t.rows[0].cells[i].text=v
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):cells[i].text=str(v)
    props=t._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    props.append(borders)
    for ri,row in enumerate(t.rows):
        trPr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trPr.append(cant)
        if ri==0:
            repeat=OxmlElement('w:tblHeader');trPr.append(repeat)
        for ci,cell in enumerate(row.cells):
            cell.width=Inches(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcPr=cell._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),'60');e.set(qn('w:type'),'dxa');mar.append(e)
            tcPr.append(mar)
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E3E3E3' if ri==0 else ('F7F7F7' if ri%2==0 else 'FFFFFF'));tcPr.append(sh)
            for a in cell.paragraphs:
                a.paragraph_format.space_after=Pt(1);a.paragraph_format.space_before=Pt(1);a.paragraph_format.line_spacing=1.05
                a.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==0 else WD_ALIGN_PARAGRAPH.CENTER
                for r in a.runs:r.font.name='Times New Roman';r.font.size=Pt(size);r.bold=ri==0;r.font.color.rgb=RGBColor(0,0,0)
    spacer=doc.add_paragraph();spacer.paragraph_format.space_after=Pt(5);spacer.paragraph_format.line_spacing=Pt(1);spacer.add_run().font.size=Pt(1)
    return t

def mathrun(text):
    r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;r.append(t);return r
def term(tag,*items):
    x=OxmlElement('m:'+tag)
    for it in items:
        if isinstance(it,str):x.append(mathrun(it))
        elif tag in ('e','num','den','sub','sup') and it.tag==qn('m:e'):
            for child in list(it):x.append(child)
        else:x.append(it)
    return x
def sub(base,s):return term('sSub',term('e',base),term('sub',s))
def sup(base,s):return term('sSup',term('e',base),term('sup',s))
def frac(a,b):return term('f',term('num',a),term('den',b))
def sqrt(a):
    rad=term('rad');pr=term('radPr');hide=OxmlElement('m:degHide');hide.set(qn('m:val'),'1');pr.append(hide);rad.append(pr);rad.append(term('deg'));rad.append(term('e',a));return rad
def overbar(a):
    pr=term('barPr');pos=OxmlElement('m:pos');pos.set(qn('m:val'),'top');pr.append(pos)
    return term('bar',pr,term('e',a))
def summation(*items):
    n=term('nary');pr=term('naryPr');ch=OxmlElement('m:chr');ch.set(qn('m:val'),'∑');pr.append(ch);loc=OxmlElement('m:limLoc');loc.set(qn('m:val'),'undOvr');pr.append(loc);n.append(pr);n.append(term('sub','t = 1'));n.append(term('sup','T'));n.append(term('e',*items));return n
def eq(items,number):
    a=doc.add_paragraph();a.alignment=WD_ALIGN_PARAGRAPH.CENTER;a.paragraph_format.space_before=Pt(5);a.paragraph_format.space_after=Pt(10)
    om=OxmlElement('m:oMath')
    for it in items:om.append(mathrun(it) if isinstance(it,str) else it)
    a._p.append(om);a.add_run('    ('+number+')').font.size=Pt(10)
def code(text):
    a=doc.add_paragraph();a.alignment=WD_ALIGN_PARAGRAPH.LEFT
    a.paragraph_format.space_before=Pt(4);a.paragraph_format.space_after=Pt(10);a.paragraph_format.line_spacing=1.0
    r=a.add_run(text);r.font.name='Courier New';r.font.size=Pt(9)
    return a
def val(scene,name,key,d=1):
    s=R[scene][name][key];return f"{s['mean']:.{d}f} ± {s['half95']:.{d}f}"
def summary(scene,extra=False):
    names=['Uniform random','Greedy','Epsilon 0.10','UCB1']+(['Epsilon alpha 0.10'] if extra else [])
    labels={'Uniform random':'Uniform random','Greedy':'Greedy','Epsilon 0.10':'ε-greedy, ε = 0.10','UCB1':'UCB1','Epsilon alpha 0.10':'ε-greedy, α = 0.10'}
    return [[labels[n],val(scene,n,'reward',4),val(scene,n,'regret',1),f"{R[scene][n]['tail_optimal']['mean']:.1f}%"] for n in names]

# PAGE 1 — source-derived formal cover.
doc._element.body.insert(0,logo)
lp=doc.paragraphs[0];lp.alignment=WD_ALIGN_PARAGRAPH.CENTER;lp.paragraph_format.space_after=Pt(20)
for line in ['SRM Institute of Science and Technology','Tiruchirappalli – 621 105','School of Computing','Artificial Intelligence and Machine Learning']:
    a=p(line,True,True);a.paragraph_format.space_after=Pt(5)
sp=p();sp.paragraph_format.space_after=Pt(28)
a=p('Comparative Analysis of ε-Greedy and UCB Algorithms for Sequential Decision Making',True,True,'Title');a.paragraph_format.space_after=Pt(18)
p('PROJECT REPORT',True,True)
p('Main Topic: Action Selection',False,True)
sp=p();sp.paragraph_format.space_after=Pt(14)
for line in ['Registration No: RA2311026050020','Student Name: PARVATHY O K','Section: B']:
    a=p(line,True,True);a.paragraph_format.space_after=Pt(7)
sp=p();sp.paragraph_format.space_after=Pt(12)
p('Code / Subject Name',True,True)
p('21CSE417TA / Fundamentals of Reinforcement Learning',True,True)
sp=p();sp.paragraph_format.space_after=Pt(42)
a=p('Student Signature                                                   Faculty Signature',True,True)
for r in a.runs:r.font.size=Pt(10)

# PAGE 2
page('Abstract')
p('This project examines how ε-greedy and Upper Confidence Bound action selection balance learning and reward in a ten-armed bandit. Both methods estimate an action’s value from the rewards observed when that action is chosen. Their difference lies in exploration: ε-greedy occasionally chooses an action uniformly at random, whereas UCB1 adds a count-dependent uncertainty bonus to each estimated value.')
p('The study uses reproducible Bernoulli simulations with 500 independent runs of 10,000 decisions per scenario. Two stationary environments test well-separated and closely matched reward probabilities. A third environment reverses the reward probabilities after 5,000 decisions. Uniform random selection and greedy selection provide baselines. A separate parameter study uses 300 runs of 5,000 decisions for each environment. All primary policies receive the same initialization and use sample-mean value estimates.')
p('With well-separated rewards, UCB1 records mean cumulative pseudo-regret of 359.4, compared with 398.4 for ε-greedy at ε = 0.10. With closely matched rewards, the ranking reverses: ε-greedy records 184.0, compared with 399.9 for UCB1. In the reversal scenario, UCB1 records 415.4, while sample-mean ε-greedy records 2,930.1. Replacing the latter’s sample mean with a constant step size of 0.10 reduces its regret to 637.8. These values describe the specified simulations and do not establish a universal ranking.')
p('The main conclusion is that action selection must be evaluated together with the reward gaps, decision horizon and value-update rule. UCB1 allocates exploration according to uncertainty and performs well when useful gaps can be resolved. Fixed ε-greedy continues to pay for uniform exploration, but can outperform the standard UCB1 coefficient over a finite horizon when the actions have similar rewards. The report presents the mathematical formulation, implementation, verification and empirical evidence supporting these conclusions.')
p('Keywords: action selection; multi-armed bandit; ε-greedy; UCB1; exploration; pseudo-regret.',False)
h('Study at a glance')
table(['Item','Setting'],[
['Primary comparison','ε = 0.10 versus UCB1 with c = √2'],
['Reward model','Bernoulli rewards in {0, 1}; ten actions'],
['Main evaluation','Three scenarios; 500 runs; 10,000 rounds'],
['Statistical reporting','Mean and approximate 95% Monte Carlo interval'],
['Verification','11 executed correctness checks; all passed']],[2.0,4.7],size=10)

# PAGE 3
page('Table of Contents')
contents=[
('Abstract','2'),('Chapter 1  Introduction','4'),('1.1 Decision setting   1.2 Exploration and exploitation   1.3 Scope','4'),
('Chapter 2  Literature Review','5'),('2.1 Foundations   2.2 Confidence methods   2.3 Changing rewards','5'),
('Chapter 3  Problem Statement and Objectives','6'),
('Chapter 4  System Analysis and Requirements','7'),
('Chapter 5  Methodology and System Design','8'),
('5.1 Bandit model   5.2 Value estimates   5.3 Action-selection rules','8'),
('5.4 Algorithm flow   5.5 Exploration behaviour','9'),
('5.6 Experimental scenarios and controls','10'),
('5.7 Evaluation measures and uncertainty','11'),
('Chapter 6  Implementation','12'),
('6.1 Simulation components   6.2 Randomness and reproducibility','12'),
('6.4 Worked decision   6.5 Updates   6.6 Computational cost','13'),
('Chapter 7  Results and Discussion','14'),
('7.1 Well-separated rewards','14'),('7.2 Closely matched rewards','15'),
('7.3 Reversal of the best action','16'),('7.4 Parameter sensitivity','17'),('7.5 Allocation patterns and interpretation','18'),
('Chapter 8  Testing and Verification','19'),
('Chapter 9  Conclusion and Future Work','20'),
('References','21'),('Appendix A  Reproduction Protocol','22')]
t=table(['Section / chapter', 'Page'], contents, [6.0, .7], size=9.5)
for row, (name, _) in zip(t.rows[1:], contents):
    if name.startswith('Chapter'):
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold=True
small('Figures: decision loop (4), experiment pipeline (7), algorithm flowcharts (9), reward rates (10), stationary performance (14–15), response to change (16), parameter sensitivity (17), action allocation (18).')

# PAGE 4
page('Chapter 1  Introduction')
h('1.1 Sequential decisions with incomplete feedback')
p('A system often has to choose an action before knowing which option is best. A recommendation service may select one item to display, or a communication system may choose one available channel. The system observes the outcome of the action it takes; it does not automatically learn what every other action would have produced. Repeating this decision creates a trade-off between collecting information and using the information already available.')
p('A multi-armed bandit isolates this action-selection problem. An action is called an arm, and its reward is a random observation with an unknown mean. In the stationary version, an action’s reward distribution stays fixed. Unlike a general Markov decision process, this experiment has no evolving state controlled by the chosen action and no delayed reward chain. Learning still affects later decisions because the agent’s estimates change with experience [1].')
link_paragraph=doc.add_paragraph('GitHub Link: ')
link_paragraph.paragraph_format.space_after=Pt(6)
link_paragraph.alignment=WD_ALIGN_PARAGRAPH.LEFT
url='https://github.com/Parvathyok/epsilon-greedy-ucb'
link=OxmlElement('w:hyperlink')
link.set(qn('r:id'),doc.part.relate_to(url,RT.HYPERLINK,is_external=True))
run=OxmlElement('w:r');properties=OxmlElement('w:rPr')
color=OxmlElement('w:color');color.set(qn('w:val'),'0000FF');properties.append(color)
underline=OxmlElement('w:u');underline.set(qn('w:val'),'single');properties.append(underline)
run.append(properties);text=OxmlElement('w:t');text.text=url;run.append(text)
link.append(run);link_paragraph._p.append(link)
fig('decision_loop','Figure 1.1  The action-selection loop and the feedback available to the learner.',6.2)
h('1.2 Exploration and exploitation')
p('Exploitation selects an action with the highest current estimated reward. Exploration samples alternatives that may be better than their present estimates suggest. A high estimate based on one success is less reliable than the same estimate based on hundreds of observations. An effective policy must decide both when to explore and which action deserves another observation.')
h('1.3 Scope of the project')
p('This report compares fixed ε-greedy with UCB1 under controlled synthetic rewards. It examines cumulative reward, pseudo-regret, best-action selection and action counts. The experiments include two stationary settings and one abrupt change. They do not model user context, delayed feedback, costs that differ by action, or a deployed application. This scope keeps the comparison focused on action selection rather than on unrelated software features.')

# PAGE 5
page('Chapter 2  Literature Review')
h('2.1 Foundations of action-value learning')
p('Sutton and Barto [1] introduce bandits as a setting for studying evaluative feedback and action-value methods. Their treatment explains greedy selection, randomized exploration and upper-confidence action selection. It also distinguishes sample-average estimation from recency-weighted estimation when rewards change. These ideas motivate the common value estimator used in the primary comparison and the constant-step diagnostic used after the reward reversal.')
h('2.2 Finite-time confidence methods')
p('Auer, Cesa-Bianchi and Fischer [2] analyse UCB1 for independent stationary rewards bounded in [0, 1]. Their result gives a gap-dependent logarithmic upper bound on expected regret. The guarantee concerns growth with the horizon under stated assumptions; it does not imply that UCB1 will outperform every alternative in a short experiment. The present study therefore separates the standard coefficient from smaller coefficients tested only in the sensitivity analysis.')
p('Bubeck and Cesa-Bianchi [3] review regret analysis for stochastic and nonstochastic bandits. Their framework distinguishes different feedback and reward assumptions. This distinction matters here: the principal experiments are stochastic, whereas the reversal scenario violates stationarity. A stationary guarantee cannot be transferred to that scenario simply because the same policy is used.')
h('2.3 Changing rewards and further confidence methods')
p('Garivier and Moulines [4] study discounted and sliding-window UCB policies for switching bandits. These methods reduce the influence of old observations. They provide a useful direction for extending the present reversal experiment; neither method is included in the numerical ranking reported here.')
p('Garivier and Cappé [5] develop KL-UCB, which uses an information-based confidence construction. Its treatment of bounded rewards suggests a more specific comparator for Bernoulli observations. This report retains UCB1 as the primary confidence method so that its count-based exploration term can be inspected directly.')
table(['Source','Relevance to this report'],[
['Sutton and Barto [1]','Action values, exploration and value updates'],
['Auer et al. [2]','UCB1 rule and stationary regret guarantee'],
['Bubeck and Cesa-Bianchi [3]','Regret definitions and model assumptions'],
['Garivier and Moulines [4]','Forgetting old observations after a change'],
['Garivier and Cappé [5]','A possible Bernoulli-specific extension']],[2.1,4.6],'Table 2.1  Literature used to define and interpret the comparison.')
h('2.4 Purpose of the comparison')
p('The contribution is a transparent comparative experiment, not a new bandit algorithm. Keeping the environment, initialization and evaluation consistent makes it possible to explain observed differences through the selection and update rules. Reporting scenarios in which the ranking changes is part of that comparison.')

# PAGE 6
page('Chapter 3  Problem Statement and Objectives')
h('3.1 Problem statement')
p('Given ten actions with unknown reward probabilities and a fixed decision budget, select one action at each round to obtain as much reward as possible. The learner sees only the selected reward. It must estimate action quality from incomplete and noisy evidence while spending part of its budget on exploration. The comparison asks how the exploration mechanism changes the total cost of selecting suboptimal actions.')
p('The primary policies are ε-greedy with ε = 0.10 and UCB1 with its standard exploration coefficient. Both start with zero estimates, sample every action once, and then update the selected estimate using the sample mean. Uniform random and purely greedy selection establish the cost of exploring without learning and exploiting without continued exploration.')
h('3.2 Research questions')
p('The first question is whether uncertainty-based exploration improves cumulative performance when one action has a clear advantage. The second is whether that advantage persists when reward probabilities are close. The third is how the policies respond when the best action changes after substantial learning. A final question concerns the sensitivity of finite-horizon results to the exploration parameter.')
h('3.3 Project objectives')
for text in [
'1. Define a bounded stochastic bandit model and implement the two selection rules without giving the policies access to the true reward means.',
'2. Use identical initialization, reward generation and run counts so that differences in measured performance can be interpreted.',
'3. Measure reward, cumulative pseudo-regret, best-action frequency and action allocation rather than relying on a single learning curve.',
'4. Quantify variation across independent runs and report paired differences for the primary comparison.',
'5. Check the update rules, tie handling, initialization, random seeds and regret calculation with executable tests.',
'6. Identify the limits of the findings and propose extensions that address those limits.']:p(text)
h('3.4 Assumptions and acceptance criteria')
p('Rewards are immediate and binary. Actions have equal cost, and each scenario has a known, fixed number of actions. Within each stationary segment, reward draws are independent. The simulator knows the reward probabilities for evaluation, while the policy receives only its own estimates, counts and round number. A complete run must contain exactly one action and one update per round, produce finite estimates, and reproduce its output under the same seed and software versions.')

# PAGE 7
page('Chapter 4  System Analysis and Requirements')
h('4.1 Experimental system')
p('The implementation is a local numerical experiment. Configuration defines the environment and policies. A reward generator creates potential outcomes, the runner exposes only the chosen outcome, and a separate evaluator computes performance. The separation in Figure 4.1 prevents the true means from influencing action selection.')
fig('experiment_pipeline','Figure 4.1  Simulation components and the boundary between learning and evaluation.',6.15)
h('4.2 Functional requirements')
table(['Component','Required behaviour'],[
['Environment','Generate independent Bernoulli outcomes; apply a change only at the specified round.'],
['Policy','Choose one valid action from current estimates, counts and round number.'],
['Estimator','Update only the selected action; preserve all other estimates.'],
['Evaluator','Accumulate reward, pseudo-regret, optimal selections and action counts.'],
['Aggregator','Retain run-level totals and compute means and uncertainty intervals.']],[1.35,5.35],'Table 4.1  Responsibilities of the experimental components.',10)
h('4.3 Software and resource requirements')
p('The executed study uses Python '+R['metadata']['python']+' and NumPy '+R['metadata']['numpy']+'. Figures are produced as vector drawings and inserted at 300 dpi. A CPU is sufficient; no GPU, network service or external dataset is required. The runner stores one reward matrix per round instead of all potential outcomes across the full horizon. This keeps memory use proportional to the number of runs, actions and policies rather than to the full simulation history.')

# PAGE 8
page('Chapter 5  Methodology and System Design')
h('5.1 Bandit model and notation')
p('Let K = 10 be the number of actions and T the number of rounds. At round t, the learner selects Aₜ and receives Rₜ ∈ {0, 1}. The reward probability of action a is μₐ. The best mean is μ* = maxₐ μₐ, and the gap of action a is Δₐ = μ* − μₐ. Counts and estimates used for selection contain observations strictly before round t.')
eq([sub('R','t'),' | ',sub('A','t'),' = a  ∼  Bernoulli(',sub('μ','a'),')'],'5.1')
table(['Symbol','Meaning'],[['K, T','Number of actions and decision horizon'],['Aₜ, Rₜ','Action and observed reward at round t'],['Nₜ(a), Qₜ(a)','Count and reward estimate before round t'],['μₐ, μ*, Δₐ','Action mean, best mean and suboptimality gap'],['ε, c, α','Random exploration rate, UCB coefficient and update step size']],[1.55,5.15],'Table 5.1  Notation used in the algorithm descriptions.',10)
h('5.2 Incremental value estimation')
p('After choosing action a and observing a reward, its count increases by one. The new estimate is obtained from the previous estimate and the prediction error. Unselected actions are unchanged. This update equals the arithmetic mean of all rewards observed for that action and avoids storing its complete reward history.')
eq([sub('Q','t+1'),'(a) = ',sub('Q','t'),'(a) + ',frac('1',term('e',sub('N','t'),'(a) + 1')),' [',sub('R','t'),' − ',sub('Q','t'),'(a)]'],'5.2')
h('5.3 Action-selection rules')
p('After the first ten initialization rounds, ε-greedy chooses a uniformly random action with probability ε and a largest-estimate action otherwise. Random exploration includes the greedy action. If the greedy action is unique, its selection probability is 1 − ε + ε/K; every other action has probability ε/K. Equal estimates are resolved uniformly at random.')
eq([sub('A','t'),' = ',sub('arg max','a'),' [',sub('Q','t'),'(a) + c',sqrt(frac('ln t',term('e',sub('N','t'),'(a)'))),']'],'5.3')
p('Equation (5.3) defines the UCB family used here. UCB1 sets c = √2. The count-dependent term is larger for actions with fewer observations. Every action is sampled once before this expression is used, so its denominator is positive. A UCB score can exceed one; it is an optimistic index and is not clipped to the reward range.')

# PAGE 9
page('Chapter 5  Methodology and System Design')
h('5.4 Algorithm flow')
fig('policy_flowcharts','Figure 5.1  The two selection rules share initialization, feedback and estimation.',6.35)
h('5.5 Expected exploration behaviour')
p('For fixed ε, exploration continues even after the correct action has been identified. In a stationary environment, the expected regret contributed by the random branch after initialization is ε/K times the sum of the action gaps per round. Additional regret occurs whenever the greedy branch selects an incorrect action. In the well-separated scenario, ε = 0.10 therefore incurs a continuing random-exploration cost of 0.036 reward units per round.')
p('UCB1 does not reserve a fixed fraction of decisions for uniform exploration. Its bonus decreases as an action accumulates observations and increases slowly with the round number. Once evidence separates the actions, the policy can spend more decisions on the best one. For stationary independent bounded rewards with fixed positive gaps, its established expected-regret bound grows logarithmically with the horizon [2]. That guarantee does not specify the winner at T = 10,000, particularly when gaps are small.')
p('The parameter experiment also tests εₜ = min(1, 1/√t). This is an illustrative decreasing schedule, not a claim of a tuned or universally optimal decay rule. All primary comparisons retain their parameters throughout a run.')

# PAGE 10
page('Chapter 5  Methodology and System Design')
h('5.6 Experimental scenarios and controls')
p('Each main scenario contains 500 independent runs of 10,000 rounds. Actions are numbered 1 through 10. Rewards are sampled from the probabilities in Table 5.2. The two stationary scenarios differ in the gap between the best and second-best action: 0.20 in the well-separated case and 0.02 in the closely matched case.')
table(['Action','Well-separated','Closely matched','After reversal'],[[str(i+1),f'{R["metadata"]["stationary_wide"][i]:.2f}',f'{R["metadata"]["stationary_close"][i]:.2f}',f'{R["metadata"]["stationary_wide"][9-i]:.2f}'] for i in range(10)],[.65,1.95,1.95,2.15],'Table 5.2  Exact Bernoulli reward probabilities.',9.5)
fig('reward_rates','Figure 5.2  Reward profiles used in the two stationary scenarios.',5.1)
p('In the reversal scenario, the well-separated vector applies through round 5,000 and its reverse applies from round 5,001. Action 10 is initially best; action 1 becomes best. The best achievable mean remains 0.70. Policies are not told about the change, and their estimates are not reset.')
p('All policies sample actions 1 to 10 once before normal selection. Within a run and round, they share the same potential reward for each action, but each sees only its chosen reward. Policy randomization uses separate streams. Runs are independent, and environment seeds differ across scenarios. This design supports paired comparisons without exposing unchosen rewards.')

# PAGE 11
page('Chapter 5  Methodology and System Design')
h('5.7 Evaluation measures')
p('Mean reward per round is total observed reward divided by the horizon. It is directly interpretable for binary rewards as the fraction of decisions receiving reward one. Pseudo-regret measures the expected opportunity cost of the selected actions using the known simulation means; it removes the extra variation caused by the realised reward draw.')
eq([sup('L','(i)'),'(', 'T', ') = ',summation('[',sup('μ','*'),' − ',sub('μ',sub('A','t')),']')],'5.4')
p('Here i denotes a run. The reported stationary pseudo-regret is the mean of L⁽ⁱ⁾(T) across runs. It is nonnegative for every action sequence. It differs from realised regret Tμ* − ΣRₜ, which contains reward noise and can occasionally be negative. In the changing environment, the evaluator uses the best mean and chosen-action mean at the current round, giving dynamic pseudo-regret.')
eq([sub(sup('L','(i)'),'dynamic'),'(T) = ',summation('[',sub(sup('μ','*'),'t'),' − ',sub('μ','t'), '(',sub('A','t'),') ]')],'5.5')
p('Best-action selection is the proportion of rounds assigned to the action with the largest true mean. The report also gives this proportion over the last 1,000 rounds. Action counts reveal where exploration is spent. Reward curves use non-overlapping 100-round blocks; regret curves show cumulative values at those same checkpoints. Blocking is a plotting choice and does not change any totals.')
h('5.8 Uncertainty and paired comparisons')
p('For a run-level measure X, the report gives its mean with an approximate 95% Monte Carlo interval. The sample standard deviation is computed across independent runs with the usual n − 1 denominator. The interval describes simulation variation for the fixed scenario, not uncertainty over all possible bandit environments.')
eq(['Interval = ',overbar('X'),' ± 1.96 ',frac('s',sqrt('n'))],'5.6')
p('Primary policy differences use Dᵢ = Lᵢ(UCB1) − Lᵢ(ε-greedy) within each matched run, followed by the same interval calculation on D. Negative values favour UCB1. Bands on learning curves are pointwise intervals, not simultaneous bands. Parameter sweeps are exploratory and are not adjusted for multiple comparisons; selecting a coefficient from them would require a separate validation study.')
h('5.9 A check on interpretation')
p('In the well-separated environment, uniform selection has expected mean reward 0.34 and pseudo-regret 10,000 × (0.70 − 0.34) = 3,600. The measured mean regret is 3,601.0. Agreement with this analytic baseline provides a direct check on the environment and evaluation logic.')

# PAGE 12
page('Chapter 6  Implementation')
h('6.1 Simulation components')
p('The implementation stores one row per independent run and one column per action. For each policy, Q holds floating-point estimates and N holds integer counts. A round is processed for all runs together using NumPy arrays. This vectorization changes execution speed but does not allow information to pass between runs.')
table(['Component','Implementation responsibility'],[
['choose','Applies forced initialization, random selection, ε-greedy or the UCB index.'],
['update','Increments selected counts and updates only selected estimates.'],
['experiment','Generates rewards, advances policies and accumulates evaluation measures.'],
['ci','Calculates a run-level mean and its Monte Carlo interval half-width.'],
['Figure builder','Reads saved results and draws diagrams, curves and uncertainty intervals.']],[1.4,5.3],'Table 6.1  Responsibilities of the implemented routines.',10)
h('6.2 Randomness and reproducibility')
p('The environment generator uses NumPy default_rng with SeedSequence([seed, 0]). Policy j uses SeedSequence([seed, j + 1]), where j starts at zero. The main policy order is uniform random, greedy, ε-greedy and UCB1. The constant-step ε-greedy variant is appended only in the reversal scenario. A shared matrix of independent uniform numbers is converted into potential Bernoulli rewards once per round.')
code('for t in 1 .. T:\n    means = current_reward_probabilities(t)\n    outcomes = environment_rng.random((runs, K)) < means\n    for policy in policies:\n        action = choose(Q, N, t, policy, policy_rng)\n        reward = outcomes[run_index, action]\n        update_selected_estimate(Q, N, action, reward)\n        accumulate_reward_and_regret(action, reward, means)')
p('The policy routine never receives means or the full outcomes matrix. Evaluation happens after the action has been selected. Exact estimate ties use independent random priorities restricted to the tied actions; numerical perturbations are not added to unequal values.')
h('6.3 Recorded outputs')
p('For each policy and scenario, the run records total reward, cumulative pseudo-regret, optimal-selection count, last-1,000-round optimal selections, post-change regret and final action counts. Checkpoints retain 100-round reward and optimal-selection measures. Run-level regret totals are retained for paired comparisons, so the uncertainty of a difference is calculated directly rather than inferred from two separate intervals.')
p('The accompanying epsilon-greedy-ucb repository includes a local browser dashboard. It displays the saved study and accepts new simulation settings. These additional comparisons do not overwrite the report data. The repository also contains the numerical code, tests, CSV exports, figure sources and report generator.')

# PAGE 13
page('Chapter 6  Implementation')
h('6.4 Worked action-selection example')
p('Consider a three-action illustration at round 100. The counts sum to 99, and the estimates shown in Table 6.2 are the information available before the next decision. The illustration is separate from the ten-action experiments and is used only to make the selection calculation explicit.')
table(['Action','Estimate Q','Count N','UCB1 bonus','UCB1 score'],[
['1','0.629','70',f'{math.sqrt(2*math.log(100)/70):.3f}',f'{44/70+math.sqrt(2*math.log(100)/70):.3f}'],
['2','0.600','25',f'{math.sqrt(2*math.log(100)/25):.3f}',f'{.6+math.sqrt(2*math.log(100)/25):.3f}'],
['3','0.500','4',f'{math.sqrt(2*math.log(100)/4):.3f}',f'{.5+math.sqrt(2*math.log(100)/4):.3f}']],[.65,1.25,1.0,1.9,1.9],'Table 6.2  A calculation showing how uncertainty changes a decision.')
p('Greedy selection chooses action 1 because it has the largest current estimate. With ε = 0.10, ε-greedy chooses action 1 with probability 0.90 + 0.10/3 = 0.9333 and each alternative with probability 0.0333. UCB1 chooses action 3 because its uncertainty bonus outweighs its lower estimate. This does not mean action 3 is known to be better; it means another observation is valuable under the UCB rule.')
h('6.5 Updating an estimate')
p('The estimates correspond to 44, 15 and 2 successes respectively. If action 3 produces reward one, its count becomes five. Its sample-mean estimate changes from 0.50 to 0.50 + (1 − 0.50)/5 = 0.60. The other two estimates remain unchanged. This is the same update used in the primary simulation.')
p('For the constant-step diagnostic, the update is Q ← Q + α(R − Q), with α = 0.10. A reward of one changes an estimate of 0.50 to 0.55 regardless of how many past rewards were observed. This places more weight on recent outcomes than a sample mean after many selections, at the cost of persistent variation under stationary rewards.')
h('6.6 Computational cost')
p('Both implemented primary rules scan all K action values, giving O(K) selection time per round and O(K) state per run. Updating one selected action takes O(1). UCB1 additionally evaluates a square root for each index. Uniform exploration itself is inexpensive, but finding and resolving a greedy maximum still requires a scan in this implementation.')
p('For n runs and P policies, the main arrays require O(nKP) storage. The temporary potential-reward matrix requires O(nK). Checkpoint summaries require O(PT/100) storage, and the run-level totals require O(nP). No timing comparison is used to rank the policies because language overhead and vectorization would confound a simple runtime claim.')

# PAGE 14
page('Chapter 7  Results and Discussion')
h('7.1 Well-separated rewards')
p('The first scenario has a best reward probability of 0.70 and a second-best probability of 0.50. UCB1 has lower final pseudo-regret than ε-greedy at ε = 0.10. The paired difference is −39.0 ± 6.4 reward units, an approximate 95% Monte Carlo interval. This is a 9.8% reduction relative to the ε-greedy mean in this scenario.')
fig('wide_performance','Figure 7.1  Well-separated rewards. Shading shows pointwise 95% intervals; reward uses 100-round blocks. The dotted line marks the best mean reward.',6.7)
table(['Policy','Mean reward','Pseudo-regret','Best action\nlast 1,000'],summary('wide'),[1.8,1.65,1.75,1.5],'Table 7.1  Well-separated rewards over 10,000 rounds. Values use mean ± 95% interval half-width.',9.5)
p('UCB1 spends more decisions on exploration early in the run, but its regret curve becomes flatter as the evidence improves. During the last 1,000 rounds it selects the best action 97.1% of the time, compared with 90.9% for ε-greedy. The latter value is close to 1 − ε + ε/K = 0.91, the probability obtained when its greedy choice is correct.')
p('The full-horizon best-action proportions are 88.8% for UCB1 and 89.4% for ε-greedy. This apparent reversal is consistent with lower regret for UCB1: regret depends on which suboptimal actions are selected, not only on the number of nonoptimal decisions. Greedy selection has a much wider interval because some runs commit to an inferior action after early outcomes.')

# PAGE 15
page('Chapter 7  Results and Discussion')
h('7.2 Closely matched rewards')
p('The second scenario has reward probabilities between 0.40 and 0.50 and a best-versus-second-best gap of only 0.02. At the same horizon, ε-greedy has substantially lower pseudo-regret than standard UCB1. The paired UCB1-minus-ε-greedy difference is 215.9 ± 10.2. Here the ε-greedy mean regret is 54.0% below the UCB1 mean.')
fig('close_performance','Figure 7.2  Closely matched rewards under the same horizon and run count. Shading shows pointwise 95% intervals; the dotted line marks the best mean.',6.7)
table(['Policy','Mean reward','Pseudo-regret','Best action\nlast 1,000'],summary('close'),[1.8,1.65,1.75,1.5],'Table 7.2  Closely matched rewards over 10,000 rounds.',9.5)
p('UCB1 continues to allocate many decisions to competing actions because differences in their estimates remain small relative to the confidence bonuses. The policy is cautious about eliminating actions, which limits its best-action frequency during this finite experiment. ε-greedy concentrates its nonrandom decisions more strongly, although it also fails to identify the best action in some runs.')
p('A low best-action frequency need not imply a large reward deficit when the alternatives are close. For this reason, pseudo-regret and mean reward are more informative than best-action frequency alone. The result does not contradict the stationary logarithmic guarantee: a bound on long-run growth does not impose an ordering between algorithms at every finite horizon or for every gap configuration.')

# PAGE 16
page('Chapter 7  Results and Discussion')
h('7.3 Reversal of the best action')
p('At round 5,001, all reward probabilities are reversed. UCB1 has the lowest dynamic pseudo-regret among the tested policies in this particular change pattern. Sample-mean ε-greedy is slow to recover, while the constant-step variant responds more effectively. Figure 7.3 measures selection of the action that is best at the current round.')
fig('switch_performance','Figure 7.3  Best-action selection in non-overlapping 100-round blocks before and after the reversal. Each curve is a mean over 500 runs.',6.7)
table(['Policy','Mean reward','Dynamic regret','Best action\nlast 1,000'],summary('switch',True),[1.8,1.65,1.75,1.5],'Table 7.3  Reversal scenario over 10,000 rounds.',9.3)
p('The measured post-change regret is 2,705.8 for sample-mean ε-greedy, 114.0 for UCB1 and 344.2 for constant-step ε-greedy. Old observations dominate the sample mean of frequently selected actions. Meanwhile, ε-greedy revisits a specific alternative through its random branch on only about ε/K = 0.01 of decisions, delaying the recognition of a previously poor action.')
p('UCB1 repeatedly revisits actions with lower counts. In this reversal, that behaviour helps it discover the newly strong action while evidence against the old best action accumulates. This is an interpretation of the observed curves and counts, not a general adaptation guarantee. Other change times or reward patterns may produce different results. Discounted or sliding-window methods require a separate comparison [4].')

# PAGE 17
page('Chapter 7  Results and Discussion')
h('7.4 Parameter sensitivity')
p('A separate study uses 300 runs and 5,000 rounds per stationary scenario. It varies ε while retaining sample-mean updates, and varies c in Q + c√(ln t/N). The main experiment’s parameters remain fixed. Figure 7.4 shows why choosing an exploration setting without reference to the environment can be misleading.')
fig('parameter_sensitivity','Figure 7.4  Exploration settings and final pseudo-regret. Error bars are approximate 95% Monte Carlo intervals. The standard UCB1 coefficient is c = √2 ≈ 1.414.',6.7)
table(['Setting','Well-separated regret','Closely matched regret'],[
['ε = 0.01',val('sensitivity_wide','eps=0.01','regret'),val('sensitivity_close','eps=0.01','regret')],
['ε = 0.05',val('sensitivity_wide','eps=0.05','regret'),val('sensitivity_close','eps=0.05','regret')],
['ε = 0.10',val('sensitivity_wide','eps=0.10','regret'),val('sensitivity_close','eps=0.10','regret')],
['ε = 0.20',val('sensitivity_wide','eps=0.20','regret'),val('sensitivity_close','eps=0.20','regret')],
['εₜ = min(1, 1/√t)',val('sensitivity_wide','decay','regret'),val('sensitivity_close','decay','regret')],
['UCB c = 0.50',val('sensitivity_wide','c=0.500','regret'),val('sensitivity_close','c=0.500','regret')],
['UCB1 c = √2',val('sensitivity_wide','c=1.414','regret'),val('sensitivity_close','c=1.414','regret')]],
[2.1,2.3,2.3],'Table 7.4  Selected sensitivity results at the shorter 5,000-round horizon.',9.5)
p('Very small ε reduces continued exploration but increases the risk of an early poor commitment. Larger ε explores more reliably but pays a continuing cost. For UCB, smaller c can improve finite-horizon performance here; the best plotted coefficient differs between the two reward profiles. Such variants are not the standard UCB1 policy and do not inherit its stated coefficient-specific guarantee. These exploratory results are not an independently validated tuning recommendation.')

# PAGE 18
page('Chapter 7  Results and Discussion')
h('7.5 Action allocation explains the regret difference')
p('Figure 7.5 shows average selections of the nine suboptimal actions in the well-separated environment. The best action is omitted to make the smaller counts readable. The action probabilities increase from action 1 to action 10, so actions near the right edge are stronger competitors.')
fig('arm_allocation','Figure 7.5  Mean selections of suboptimal actions over 10,000 rounds.',5.3)
p('Uniform exploration revisits every action regardless of how clearly it has been outperformed. UCB1 concentrates more visits on competitive alternatives. A near-best action and a poor action count equally as nonoptimal decisions but incur different regret, explaining why best-action frequency alone can misrepresent performance.')
h('7.6 Comparison across the three scenarios')
table(['Scenario','UCB1 minus ε-greedy regret','Lower mean regret'],[
['Well-separated','−39.0 ± 6.4','UCB1'],
['Closely matched','215.9 ± 10.2','ε-greedy'],
['Reversal','−2,514.8 ± 20.7','UCB1']],[1.8,2.8,2.1],'Table 7.5  Paired differences across 500 runs at T = 10,000.',10)
p('The standard confidence bonus is useful in the well-separated and specified reversal environments, but explores too broadly to beat ε-greedy within the closely matched experiment’s budget. Parameter and update choices depend on the problem.')
h('7.7 Limits of the evidence')
p('The reward vectors are fixed and synthetic; the intervals do not cover variation across real applications. The study tests one action count, two main reward-gap profiles and one change pattern. The reversal is not representative of every nonstationary process. No user context, delayed outcomes, action costs or adversarial reward generation is included. Broader claims would require more environments and a separate tuning and evaluation protocol.')

# PAGE 19
page('Chapter 8  Testing and Verification')
h('8.1 Executed correctness checks')
p('Eleven automated checks were executed before the report was assembled. They test calculations with known answers and behaviour at important boundaries. All eleven passed. The simulation also checks that every run contains exactly T selections and that its value estimates remain finite and within [0, 1].')
table(['ID','Check','Expected evidence','Result'],[
['T01','Sample-mean update','Rewards 1, 0, 1, 1 give estimate 0.75.','PASS'],
['T02','UCB uncertainty','A sparsely sampled action wins the known index comparison.','PASS'],
['T03','Initialization','Every action has count one after K rounds.','PASS'],
['T04','ε = 0','Every selected action is the unique greedy maximum.','PASS'],
['T05','ε = 1','30,000 selections are within 0.015 of uniform proportions.','PASS'],
['T06','Equal-value ties','No first-action bias within the same frequency tolerance.','PASS'],
['T07','Constant step size','Q = 0.50, R = 1, α = 0.10 gives Q = 0.55.','PASS'],
['T08','Equal true means','Pseudo-regret is exactly zero.','PASS'],
['T09','Seed reproducibility','Repeated runs with the same seed match exactly.','PASS'],
['T10','Interval calculation','Mean and standard error match a hand calculation.','PASS'],
['T11','Dynamic benchmark','A two-round changing optimum yields zero regret when followed.','PASS']],[.5,1.45,4.05,.7],'Table 8.1  Executed algorithm and evaluation checks.',9.5)
h('8.2 Integration and analytical checks')
p('The independent-run count is the statistical unit for uncertainty estimates. Checkpoint averages are not treated as additional independent runs. The random baseline agrees with its analytic expectation: its well-separated mean regret is 3,601.0 against an expectation of 3,600, and its closely matched mean regret is 540.1 against an expectation of 540. The last-round counts sum to 10,000 in every main run.')
h('8.3 What the checks establish')
p('These checks support the correctness of the implemented selection, updating and measurement logic for the tested cases. They do not prove a regret theorem or certify performance in a deployed system. The parameter sweep is interpreted descriptively, and the observed reversal performance is kept separate from stationary theoretical guarantees.')

# PAGE 20
page('Chapter 9  Conclusion and Future Work')
h('9.1 Conclusion')
p('This project compared ε-greedy and UCB1 as action-selection methods in a controlled ten-armed bandit. The comparison held initialization and the main value estimator constant, used shared potential rewards for paired evaluation, and measured outcomes across 500 independent runs per scenario. The results show that a useful comparison must state the reward gaps, horizon, exploration settings and update rule.')
p('UCB1 reduced mean pseudo-regret from 398.4 to 359.4 in the well-separated environment. In the closely matched environment, ε-greedy reduced regret from UCB1’s 399.9 to 184.0. The change in ranking is the central finding. Confidence-based exploration can spend too much of a finite budget distinguishing similar actions, even while retaining a sound stationary theoretical basis.')
p('The reversal experiment also exposed a limitation of long-memory estimation. Sample-mean ε-greedy retained outdated evidence and adapted slowly. A constant step size improved its response, while UCB1 performed best among the tested policies for this specific reversal. This result supports further study of forgetting mechanisms rather than a claim that standard UCB1 handles arbitrary change.')
h('9.2 Practical implications within the study scope')
p('For a stationary task with a clearly superior action, the uncertainty-driven allocation used by UCB1 is a reasonable baseline. For a short decision budget with closely matched actions, the exploration coefficient deserves explicit evaluation. A fixed ε is easy to interpret, but it retains an exploration cost after learning. Decreasing ε can reduce that cost while making premature commitment more consequential.')
p('An action-selection method and a value-update rule should be chosen together. When old evidence may become irrelevant, retaining every past observation with equal weight can delay recovery. Mean reward, regret and allocation counts should be examined together; a best-action percentage alone can conceal how costly the alternative selections are.')
h('9.3 Future work')
p('The first extension is to vary the number of actions, decision horizon and reward gaps across many generated environments. Parameters should be selected on one set of environments and evaluated on a separate set. Longer horizons would help show when the finite-horizon ordering changes.')
p('The second extension is to test repeated and gradual changes using discounted or sliding-window estimates. A third is to compare KL-UCB and Thompson sampling on the same Bernoulli tasks. Contextual rewards, delayed feedback and unequal action costs would move the problem closer to particular applications, but each extension requires a revised model and evaluation protocol.')
p('The report provides a reproducible basis for those extensions: explicit scenarios, original figures, uncertainty estimates and tested implementations. Its conclusions remain limited to the assumptions and experiments reported here.')

# PAGE 21
page('References')
refs=[
('[1] Sutton, R. S., and Barto, A. G. (2018). Reinforcement Learning: An Introduction. 2nd edition. MIT Press. Chapter 2, Multi-armed Bandits.','https://mitpress.mit.edu/9780262039246/reinforcement-learning/'),
('[2] Auer, P., Cesa-Bianchi, N., and Fischer, P. (2002). Finite-time Analysis of the Multiarmed Bandit Problem. Machine Learning, 47, 235–256.','https://doi.org/10.1023/A:1013689704352'),
('[3] Bubeck, S., and Cesa-Bianchi, N. (2012). Regret Analysis of Stochastic and Nonstochastic Multi-armed Bandit Problems. Foundations and Trends in Machine Learning, 5(1), 1–122.','https://arxiv.org/abs/1204.5721'),
('[4] Garivier, A., and Moulines, E. (2011). On Upper-Confidence Bound Policies for Switching Bandit Problems. Algorithmic Learning Theory, Lecture Notes in Computer Science, 6925, 174–188.','https://doi.org/10.1007/978-3-642-24412-4_16'),
('[5] Garivier, A., and Cappé, O. (2011). The KL-UCB Algorithm for Bounded Stochastic Bandits and Beyond. Proceedings of the 24th Annual Conference on Learning Theory, Proceedings of Machine Learning Research, 19, 359–376.','https://proceedings.mlr.press/v19/garivier11a.html')]
for ref,url in refs:
    a=p(ref);a.paragraph_format.space_after=Pt(3)
    a=p(url);a.alignment=WD_ALIGN_PARAGRAPH.LEFT;a.paragraph_format.space_after=Pt(17)
    for rr in a.runs:rr.font.size=Pt(10)
h('Relationship between sources and experimental evidence')
p('The cited works provide the algorithmic context and theoretical assumptions. All numerical results in Chapter 7 come from the simulation protocol described in this report. The figures are original drawings or plots of those simulation outputs. Numerical results from unrelated applications are not used as evidence for the present comparison.')
p('UCB1 denotes the coefficient c = √2 throughout the main comparison. Other values of c are identified as UCB index variants. The nonstationary results are empirical observations and are not presented as consequences of the stationary regret guarantee.')

# PAGE 22
page('Appendix A  Reproduction Protocol')
h('A.1 Exact experiment settings')
table(['Experiment','Runs','Rounds','Environment seed'],[
['Well-separated','500','10,000','20261111'],['Closely matched','500','10,000','20261112'],['Reversal','500','10,000','20261113'],
['Sensitivity, well-separated','300','5,000','20262111'],['Sensitivity, closely matched','300','5,000','20262112']],[2.7,.7,1.0,2.3],'Table A.1  Seeds and budgets for the completed experiments.',10)
p('Use the probabilities in Table 5.2. Initialize Q and N to zero. Force action t in rounds 1 to 10, then apply the policy rule. Main policies use sample-mean updates; only the additional reversal diagnostic uses α = 0.10. The change is applied before choosing and rewarding round 5,001, without resetting any policy state.')
h('A.2 Core update and selection pseudocode')
code('INITIALIZE Q[a] = 0 and N[a] = 0 for every action a\nFOR round t = 1, ..., T:\n    IF t <= K:\n        a = t\n    ELSE IF policy is epsilon-greedy:\n        IF Uniform(0, 1) < epsilon:\n            a = UniformRandomAction(1, ..., K)\n        ELSE:\n            a = RandomArgmax(Q)\n    ELSE IF policy is UCB1:\n        score[a] = Q[a] + sqrt(2 * ln(t) / N[a])\n        a = RandomArgmax(score)\n    r = reward for the selected action a\n    N[a] = N[a] + 1\n    Q[a] = Q[a] + (r - Q[a]) / N[a]\n    record r, current_best_mean - current_mean[a], a')
h('A.3 Sensitivity order and reporting')
p('Sensitivity policies are ordered as ε = 0.01, 0.05, 0.10, 0.20; εₜ = min(1, 1/√t); then UCB coefficients c = 0.25, 0.50, 1.00, √2 and 2.00. Generate the environment and policy streams as described in Section 6.2. Use the same potential-outcome matrix for every policy at each round, retaining only the selected outcome for the learner.')
p('Average results over runs, not over checkpoint summaries. For each interval, use the sample standard deviation with one degree of freedom removed and calculate 1.96s/√n. For paired comparisons, first subtract policy regrets within each run. Plot regret every 100 rounds and use non-overlapping 100-round reward blocks. Round only for display; retain full precision during aggregation.')
small('Execution environment: Python '+R['metadata']['python']+'; NumPy '+R['metadata']['numpy']+'. Random streams use NumPy default_rng and SeedSequence. Exact random draws depend on these generator choices and call order; the protocol fixes both in the implementation.')



OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print(OUT)
print('Paragraphs',len(doc.paragraphs),'tables',len(doc.tables),'figures',len(doc.inline_shapes))
