"""Freeze local evidence and generate quantitative tables/vector figures for the draft."""

from pathlib import Path
import hashlib
import json
import re
import shutil

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF, renderSVG
from reportlab.lib import colors

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EVIDENCE=HERE/'evidence/full_paper'
FIGURES=HERE/'figures'
GENERATED=HERE/'generated'
for folder in (EVIDENCE,FIGURES,GENERATED,EVIDENCE/'source_snapshot'):
    folder.mkdir(parents=True,exist_ok=True)
FINAL=ROOT/'output/dt_modular_acceptance_20261027_02'
EARLY=ROOT/'output/dt_modular_acceptance_20261027_01'
PROBES=ROOT/'output/dt_modular_grip_probes'
results=json.loads((FINAL/'results.json').read_text())
early=json.loads((EARLY/'results.json').read_text())
assert len(results)==18 and all(r['pass'] for r in results)
assert sum(r['controller_state']=='DONE' for r in results)==11
assert sum(r['controller_state']=='HOLD' for r in results)==7
by_case={r['case']:r for r in results}
probes={p.parent.name:json.loads(p.read_text()) for p in PROBES.glob('*/summary.json')}
assert len(probes)==4

# Existing front matter is preserved byte-for-byte inside its own new source.
old=(HERE/'main.tex').read_text(encoding='utf-8-sig')
title=re.search(r'\\title\[.*?\]\s*\{([^}]+)\}',old,re.S).group(1)
abstract=re.search(r'\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}',old,re.S).group(1)
assert len(abstract.split())==223
front=old.replace('\\input{introduction}\n','').replace('\\balance\n','').replace('\\input{references_list}\n','')
target=HERE/'title_abstract.tex'
if not target.exists():
    target.write_text(front,encoding='utf-8')
else:
    retained=re.search(r'\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}',target.read_text(),re.S).group(1)
    assert retained==abstract, 'Retained abstract has been edited; review before regenerating.'
prefix=old[:old.index('\\begin{document}')]
(HERE/'journal_layout.tex').write_text(prefix+'\n\\setlength{\\tabcolsep}{3pt}\n\\renewcommand{\\arraystretch}{1.12}\n',encoding='utf-8')

def esc(text):
    return str(text).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')


names={**{f'bin_{i}':f'Box {i}' for i in range(1,7)},
       'speed_low':'Low-speed handling','speed_high':'High-speed handling','strict':'Observability gate',
       'missing_ps1':'PS1 stuck low','missing_ps2':'PS2 stuck low','missing_a1_end':'A1-extended stuck low',
       'profile_geometry_slow_a2':'Geometry variant + slower A2',
       'profile_dynamics_slow_a2':'Dynamics variant + slower A2',
       'network_delay_20ms':'Delayed telemetry','network_stale':'Stale first telemetry',
       'network_loss_all':'Complete telemetry loss','network_pick_age':'Age-limited pickup'}
settings={**{f'bin_{i}':'Nominal profile; zero channel delay' for i in range(1,7)},
       'speed_low':r'$v=0.10$ m/s','speed_high':r'$v=0.24$ m/s','strict':'Open-loop assumptions disabled',
       'missing_ps1':'PS1 forced false from reset','missing_ps2':'PS2 forced false from reset',
       'missing_a1_end':'A1 extended switch forced false',
       'profile_geometry_slow_a2':r'PS2 $-5$ mm; box 1 $+5$ mm in X; A2 0.06 m/s',
       'profile_dynamics_slow_a2':r'Product mass $+10\%$; X rate $\times0.85$; A2 0.06 m/s',
       'network_delay_20ms':'20 ms configured channel delay',
       'network_stale':'80 ms delay; 50 ms maximum age',
       'network_loss_all':r'Packet-drop probability $p=1$',
       'network_pick_age':'40 ms delay; nominal age/uncertainty limits'}
lines=[r'\begin{table*}[t]',r'\centering\small',
       r'\caption{Final deterministic acceptance suite. Times are absolute simulation times in seconds. A dash means that HOLD was not entered. Every row met its specified outcome; this includes intentional holds, not eighteen production completions.}',
       r'\label{tab:cases}',r'\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}l p{.25\textwidth} p{.35\textwidth} c r r@{}}',
       r'\toprule ID & Case & Changed condition & State & HOLD (s) & End (s)\\\midrule']
for i,r in enumerate(results,1):
    hold='--' if r['hold_time_s'] is None else f"{r['hold_time_s']:.2f}"
    lines.append(f"S{i:02d} & {names[r['case']]} & {settings[r['case']]} & {r['controller_state']} & {hold} & {r['simulation_time_s']:.2f}"+r'\\')
lines += [r'\bottomrule\end{tabular*}',r'\end{table*}']
(GENERATED/'acceptance_table.tex').write_text('\n'.join(lines),encoding='utf-8')

lines=[r'\begin{table}[t]',r'\centering\small',
       r'\caption{Source-time-aligned Y-estimation errors in selected completed runs. $n_e$ counts error samples, not independent trials. The nominal row uses box 1; its pre-transfer trace is repeated across the six nominal destinations.}',
       r'\label{tab:errors}',r'\begin{tabular}{@{}p{.34\columnwidth}rrrr@{}}\toprule',
       r'Condition & $n_e$ & RMSE & $Q_{.95}$ & Max\\',r'& & \multicolumn{3}{c}{Absolute-error units: mm}\\\midrule']
labels={'speed_low':r'Nominal, 0.10 m/s','bin_1':r'Nominal, 0.16 m/s','speed_high':r'Nominal, 0.24 m/s',
        'network_delay_20ms':r'20 ms delay','profile_geometry_slow_a2':r'Geometry + slow A2',
        'profile_dynamics_slow_a2':r'Dynamics + slow A2'}
for key,label in labels.items():
    r=by_case[key]
    lines.append(f"{label} & {r['y_error_samples']} & {r['y_error_rmse_m']*1000:.3f} & {r['y_error_p95_abs_m']*1000:.3f} & {r['y_error_max_abs_m']*1000:.3f}"+r'\\')
lines += [r'\bottomrule\end{tabular}',r'\end{table}']
(GENERATED/'error_table.tex').write_text('\n'.join(lines),encoding='utf-8')

study=[]
for key,label in [('profile_geometry','Geometry'),('profile_dynamics','Dynamics')]:
    r=next(x for x in early if x['case']==key)
    study.append((label,.12,5,r['simulation_time_s'],r['placement_pass_evaluator_only']))
for key in ('geometry_slow_a2','mass_slow_a2','geometry_adhesion_10','mass_adhesion_10'):
    r=probes[key]
    study.append(('Geometry' if key.startswith('geometry') else 'Dynamics',
                  .06 if 'slow' in key else .12,5 if 'slow' in key else 10,
                  r['simulation_time_s'],r['placement_pass_evaluator_only']))
lines=[r'\begin{table}[t]',r'\centering\small',
       r'\caption{Development-stage sensitivity records, separate from the final suite. The slower-A2 settings were selected after the two initial failures; these are not held-out comparisons. All six controllers reached DONE.}',
       r'\label{tab:development}',r'\begin{tabular}{@{}lrrrr@{}}\toprule',
       r'Variant & A2 (m/s) & Adhesion (N) & End (s) & Placed\\\midrule']
for label,rate,force,t,placed in study:
    lines.append(f"{label} & {rate:.2f} & {force} & {t:.2f} & {'Yes' if placed else 'No'}"+r'\\')
lines += [r'\bottomrule\end{tabular}',r'\end{table}']
(GENERATED/'development_table.tex').write_text('\n'.join(lines),encoding='utf-8')

FONT=HERE/'open_fonts/CharisSIL-Regular.ttf'
pdfmetrics.registerFont(TTFont('Paper',str(FONT)))
BLUE=colors.HexColor('#175B83'); TEAL=colors.HexColor('#187B70'); GRAY=colors.HexColor('#444444')

def text(d,x,y,s,size=8.5,anchor='start'):
    d.add(String(x,y,s,fontName='Paper',fontSize=size,textAnchor=anchor,fillColor=colors.black))


def arrow(d,x1,y1,x2,y2,color=GRAY):
    d.add(Line(x1,y1,x2,y2,strokeColor=color,strokeWidth=.8))
    if x1==x2:
        sign=1 if y2>y1 else -1; points=[x2,y2,x2-2.5,y2-5*sign,x2+2.5,y2-5*sign]
    else:
        sign=1 if x2>x1 else -1; points=[x2,y2,x2-5*sign,y2-2.5,x2-5*sign,y2+2.5]
    d.add(Polygon(points,strokeColor=color,fillColor=color))


def node(d,x,y,w,h,lines,dashed=False):
    d.add(Rect(x,y,w,h,rx=3,ry=3,fillColor=colors.HexColor('#F2F5F7'),strokeColor=GRAY,
               strokeWidth=.7,strokeDashArray=[3,2] if dashed else None))
    for i,s in enumerate(lines): text(d,x+w/2,y+h/2+(len(lines)-1)*5.5-i*11-3,s,anchor='middle')


def save(d,name):
    renderPDF.drawToFile(d,str(FIGURES/(name+'.pdf')))
    renderSVG.drawToFile(d,str(FIGURES/(name+'.svg')))


d=Drawing(510,175)
for x,w,label in [(2,82,['MuJoCo plant']),(105,82,['Sensor model']),(208,82,['Channel /','receiver']),
                  (311,88,['State estimate','and sequencer'])]: node(d,x,111,w,37,label)
for a,b in [(84,105),(187,208),(290,311)]: arrow(d,a,129,b,129)
node(d,422,111,86,37,['Issued commands'])
arrow(d,399,129,422,129)
for x1,y1,x2,y2 in [(465,111,465,92),(465,92,43,92),(43,92,43,111)]: arrow(d,x1,y1,x2,y2)
text(d,254,81,'Actuator path: no ground-truth product pose supplied to the controller',8,anchor='middle')
node(d,197,21,138,35,['Independent evaluator'])
arrow(d,43,111,43,38); arrow(d,43,38,197,38)
text(d,58,48,'Ground truth',8)
arrow(d,356,111,356,38); arrow(d,356,38,335,38)
text(d,367,50,'Estimates',8)
text(d,2,163,'Profile: SI parameters, provenance and run-specific MJCF',9)
node(d,391,21,117,35,['Multi-scenario planning','(proposed, not tested)'],dashed=True)
save(d,'architecture')


def plot(d,data,xmin,xmax,ymin,ymax,xticks,yticks,ylabel,xlabel,labels):
    p=LinePlot(); p.x=48; p.y=36; p.width=450; p.height=112; p.data=data
    p.xValueAxis.valueMin=xmin; p.xValueAxis.valueMax=xmax; p.xValueAxis.valueSteps=xticks
    p.yValueAxis.valueMin=ymin; p.yValueAxis.valueMax=ymax; p.yValueAxis.valueSteps=yticks
    for axis in (p.xValueAxis,p.yValueAxis):
        axis.labels.fontName='Paper'; axis.labels.fontSize=8; axis.strokeWidth=.6
    for i,(label,color,dash) in enumerate(labels):
        p.lines[i].strokeColor=color; p.lines[i].strokeWidth=1
        if dash: p.lines[i].strokeDashArray=dash
        x=48+i*150
        d.add(Line(x,169,x+17,169,strokeColor=color,strokeWidth=1,strokeDashArray=dash))
        text(d,x+21,166,label,8)
    d.add(p)
    text(d,48,188,ylabel,9)
    text(d,274,9,xlabel,8.5,anchor='middle')


d=Drawing(510,198)
curves=[]
for case in ('speed_low','bin_1','speed_high'):
    rows=[json.loads(l) for l in (FINAL/case/'ground_truth.jsonl').read_text().splitlines()]
    points=[(r['time_s'],r['y_estimation_error_m']*1000) for r in rows if r['y_estimation_error_m'] is not None]
    first=points[0][0]
    curves.append([(t-first,e) for t,e in points])
plot(d,curves,0,3.1,-2,2,[0,.5,1,1.5,2,2.5,3],[-2,-1,0,1,2],
     'Signed longitudinal estimation error (mm)','Simulation time since first valid PS1 anchor (s)',
     [('0.10 m/s',GRAY,[4,2]),('0.16 m/s',BLUE,None),('0.24 m/s',TEAL,[1,2])])
save(d,'estimation_error')


def lift_trace(folder):
    decisions=[json.loads(l) for l in (folder/'controller.jsonl').read_text().splitlines()]
    ground=[json.loads(l) for l in (folder/'ground_truth.jsonl').read_text().splitlines()]
    start=next(g['time_s'] for d,g in zip(decisions,ground) if d['phase']=='LIFT')
    return [(g['time_s']-start,g['product_xyz_m'][2]*1000) for g in ground if start <= g['time_s'] <= start+2]


d=Drawing(510,198)
plot(d,[lift_trace(EARLY/'profile_geometry'),lift_trace(PROBES/'geometry_slow_a2'),
        lift_trace(PROBES/'geometry_adhesion_10')],0,2,40,125,[0,.5,1,1.5,2],[40,60,80,100,120],
     'Simulated product-center height (mm)','Simulation time since LIFT entry (s)',
     [('A2 0.12 m/s; 5 N',GRAY,[4,2]),('A2 0.06 m/s; 5 N',BLUE,None),('A2 0.12 m/s; 10 N',TEAL,[1,2])])
save(d,'grip_sensitivity')

# Freeze the experimental records actually used by text and figures.
for source,name in [(FINAL/'results.json','final_results.json'),(EARLY/'results.json','development_results.json')]:
    shutil.copy2(source,EVIDENCE/name)
write=lambda path,obj: path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
write(EVIDENCE/'probe_results.json',probes)
paths=list((ROOT/'mujoco').glob('*.py'))+[ROOT/'mujoco/production_cell.xml',
    ROOT/'mujoco/configs/simulation.json',ROOT/'mujoco/configs/slow_a2_demo.json']
snapshots=[]
for path in paths:
    dest=EVIDENCE/'source_snapshot'/path.relative_to(ROOT/'mujoco')
    dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
    snapshots.append({'source':str(path.relative_to(ROOT)),'snapshot':str(dest.relative_to(HERE)),
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for r in results:
    manifest=json.loads((FINAL/r['case']/'manifest.json').read_text())
    for name,digest in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT/'mujoco'/name).read_bytes()).hexdigest()==digest,(r['case'],name)
write(EVIDENCE/'data_provenance.json',{
    'date':'2026-10-27','source_snapshots':snapshots,'final_suite':str(FINAL.relative_to(ROOT)),
    'development_suite':str(EARLY.relative_to(ROOT)),'probes':str(PROBES.relative_to(ROOT)),
    'final_cases':18,'production_completed':11,'intentional_holds':7,'unit_checks':25,
    'analysis':'descriptive engineering development; post-hoc selection; no held-out or physical validation',
    'front_matter':{'title':title,'abstract_words':223,'retained_without_rewriting':True},
    'human_verification':'pending','submission_ready':False})

refs=(HERE/'references_list.tex').read_text(encoding='utf-8').replace(r'\begin{thebibliography}{6}',r'\begin{thebibliography}{7}')
addition=r'''\bibitem{Kassis2026}
T.~Kassis, V.~Agarwal, Y.~He, D.~Patel, A.~M.~Brueckner,
Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents,
arXiv:2609.00065 (2026), \url{https://doi.org/10.48550/arXiv.2609.00065}.
'''
(GENERATED/'manuscript_references.tex').write_text(refs.replace(r'\end{thebibliography}',addition+r'\end{thebibliography}'),encoding='utf-8')
print('Prepared: retained front matter, three vector figures, three data-derived tables, evidence snapshots.')
