#!/usr/bin/env python3
"""
Generate concordance analysis HTML report from analysis_results.json.
"""

import json
import os
import math

OUTDIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(OUTDIR, 'analysis_results.json')) as f:
    R = json.load(f)

# Also load raw data for scatter plots and detailed computations
with open(os.path.join(OUTDIR, 'master_extract.json')) as f:
    master_raw = json.load(f)
with open(os.path.join(OUTDIR, 'grades_extract.json')) as f:
    grades_raw = json.load(f)

# Deduplicate master
seen = set()
master = []
for r in master_raw:
    lid = r.get('LASID')
    if lid and lid not in seen:
        seen.add(lid)
        master.append(r)

# Join grades
grades_by_lasid = {}
for r in grades_raw:
    if r.get('LASID'):
        grades_by_lasid[r['LASID']] = r
for r in master:
    g = grades_by_lasid.get(r.get('LASID'), {})
    r['ela_grade_pct'] = g.get('ela_pct')
    r['math_grade_pct'] = g.get('math_pct')

def sf(v):
    if v is None or v == '': return None
    try: return float(v)
    except: return None

def normalize_school(s):
    if not s: return ''
    s = s.strip()
    if 'Hughes' in s: return 'LHA'
    if 'Green' in s: return 'Green'
    if 'Ashe' in s: return 'Ashe'
    if 'Wheatley' in s: return 'Wheatley'
    return s

for r in master:
    r['school_short'] = normalize_school(r.get('school',''))

# ============================================================
# HTML GENERATION
# ============================================================

def pct(v, digits=1):
    if v is None: return '&mdash;'
    return f"{v*100:.{digits}f}%"

def num(v, digits=3):
    if v is None: return '&mdash;'
    return f"{v:.{digits}f}"

# Prepare scatter data as JS arrays
def scatter_js(data, x_field, y_field, subj):
    pts = []
    ach_field = f'leap_{subj}_ach'
    for r in data:
        x = sf(r.get(x_field))
        y = sf(r.get(y_field))
        ach = (r.get(ach_field) or '').strip()
        sch = r.get('school_short', '')
        if x is not None and y is not None and ach:
            pts.append(f"[{x:.1f},{y},'{ach}','{sch}']")
    return '[' + ','.join(pts) + ']'

scatter_anet_ela_js = scatter_js(master, 'anet_ela_eoy', 'leap_ela_ss', 'ela')
scatter_anet_math_js = scatter_js(master, 'anet_math_eoy', 'leap_math_ss', 'math')
scatter_grade_ela_js = scatter_js(master, 'ela_grade_pct', 'leap_ela_ss', 'ela')
scatter_grade_math_js = scatter_js(master, 'math_grade_pct', 'leap_math_ss', 'math')
scatter_map_ela_js = scatter_js(master, 'map_ela_pctile', 'leap_ela_ss', 'ela')

# System summary data
ss = R['system_summary']

# School concordance
sc = R['school_concordance']

# Blind spot detail
bd = R['blind_detail']

# Build the correlation comparison bar data
corr_data = R['corr_results']

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Assessment Concordance Analysis - FirstLine Schools 2024-25</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600;8..60,700&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {{
  --bg: #faf8f5;
  --ink: #1a1a1a;
  --muted: #5a6474;
  --border: #e2ddd5;
  --accent: #2d5a27;
  --red: #b33234;
  --amber: #c67f17;
  --blue: #2b6cb0;
  --green: #2d5a27;
  --purple: #6b46c1;
  --rose: #be185d;
  --ashe: #2b6cb0;
  --green-school: #2d5a27;
  --lha: #c67f17;
  --wheatley: #6b46c1;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 16px;
  line-height: 1.6;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}}

h1 {{
  font-family: 'Source Sans 3', sans-serif;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
  color: var(--ink);
}}

h2 {{
  font-family: 'Source Sans 3', sans-serif;
  font-size: 1.35rem;
  font-weight: 600;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
  color: var(--ink);
  border-bottom: 2px solid var(--border);
  padding-bottom: 0.5rem;
}}

h3 {{
  font-family: 'Source Sans 3', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--muted);
}}

.subtitle {{
  font-family: 'Source Sans 3', sans-serif;
  color: var(--muted);
  font-size: 0.95rem;
  margin-bottom: 2rem;
}}

p {{ margin-bottom: 0.75rem; }}

.finding {{
  background: #fff;
  border-left: 4px solid var(--accent);
  padding: 1rem 1.25rem;
  margin: 1rem 0;
  border-radius: 0 4px 4px 0;
}}

.finding.critical {{
  border-left-color: var(--red);
}}

.finding.warning {{
  border-left-color: var(--amber);
}}

.finding strong {{
  font-family: 'Source Sans 3', sans-serif;
}}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0 1.5rem;
  font-size: 0.9rem;
}}

th {{
  font-family: 'Source Sans 3', sans-serif;
  font-weight: 600;
  text-align: left;
  padding: 0.6rem 0.75rem;
  border-bottom: 2px solid var(--border);
  color: var(--muted);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

td {{
  font-family: 'IBM Plex Mono', monospace;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.85rem;
}}

tr:hover td {{
  background: rgba(0,0,0,0.02);
}}

td.label {{
  font-family: 'Source Sans 3', sans-serif;
  font-weight: 500;
}}

.highlight {{ background: #fef3c7; }}
.bad {{ color: var(--red); font-weight: 600; }}
.good {{ color: var(--green); font-weight: 600; }}
.muted {{ color: var(--muted); }}

.bar-container {{
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}

.bar {{
  height: 18px;
  border-radius: 2px;
  min-width: 2px;
}}

.grid-2 {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin: 1rem 0;
}}

.grid-3 {{
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}}

.card {{
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1.25rem;
}}

.card h3 {{
  margin-top: 0;
  font-size: 1rem;
}}

.matrix {{
  display: grid;
  grid-template-columns: auto 1fr 1fr;
  gap: 0;
  margin: 0.5rem 0;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.85rem;
}}

.matrix .cell {{
  padding: 0.5rem 0.75rem;
  text-align: center;
  border: 1px solid var(--border);
}}

.matrix .header {{
  font-family: 'Source Sans 3', sans-serif;
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--muted);
  background: #f5f3ef;
}}

.matrix .tp {{ background: #dcfce7; }}
.matrix .fp {{ background: #fef3c7; }}
.matrix .fn {{ background: #fce7f3; }}
.matrix .tn {{ background: #e0f2fe; }}

.stat-row {{
  display: flex;
  gap: 1.5rem;
  margin: 0.75rem 0;
  flex-wrap: wrap;
}}

.stat {{
  text-align: center;
}}

.stat .value {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 1.5rem;
  font-weight: 600;
  display: block;
}}

.stat .label {{
  font-family: 'Source Sans 3', sans-serif;
  font-size: 0.75rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

canvas {{
  border: 1px solid var(--border);
  border-radius: 4px;
  background: #fff;
}}

.scatter-container {{
  position: relative;
  margin: 1rem 0;
}}

.tooltip {{
  position: absolute;
  display: none;
  background: rgba(26,26,26,0.9);
  color: #fff;
  padding: 4px 8px;
  border-radius: 3px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem;
  pointer-events: none;
  white-space: nowrap;
  z-index: 10;
}}

.legend {{
  display: flex;
  gap: 1rem;
  margin: 0.5rem 0 0;
  font-family: 'Source Sans 3', sans-serif;
  font-size: 0.8rem;
  color: var(--muted);
  flex-wrap: wrap;
}}

.legend span {{
  display: flex;
  align-items: center;
  gap: 4px;
}}

.legend .dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}}

.heatmap {{
  width: 100%;
  border-collapse: collapse;
}}

.heatmap td {{
  text-align: center;
  font-weight: 600;
  width: 16%;
}}

.heatmap .heat-0 {{ background: #f0fdf4; color: var(--green); }}
.heatmap .heat-1 {{ background: #fef9c3; color: #92400e; }}
.heatmap .heat-2 {{ background: #fed7aa; color: #9a3412; }}
.heatmap .heat-3 {{ background: #fca5a5; color: #991b1b; }}
.heatmap .heat-4 {{ background: #f87171; color: #7f1d1d; }}

@media (max-width: 768px) {{
  .grid-2 {{ grid-template-columns: 1fr; }}
  .grid-3 {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<h1>Internal Assessments Agree on 82% of Students &mdash; But Grades Agree on Only 77%</h1>
<div class="subtitle">Assessment Concordance Analysis | FirstLine Schools | 2024-25 | n={R['n_students']:,} LEAP-tested students</div>

<div class="finding critical">
<strong>451 students (24%) carry B+ Math grades but score Unsatisfactory or Approaching Basic on LEAP.</strong>
Their course grades signal proficiency; the state test says otherwise. The anet interims correctly identified 73% of these students as at-risk. The grades did not.
</div>

<div class="finding">
<strong>anet interims and MAP are strong LEAP predictors (r = 0.63&ndash;0.84).</strong>
Course grades lag behind (r = 0.40&ndash;0.56). Among all internal measures at scale, anet Math MOY is the single best concordance predictor (86.1% agreement, n=1,700). MAP Math BOY has the highest correlation (r=0.84) but covers only 26% of students.
</div>

<h2>1. Data Coverage</h2>

<p>Of {R['n_students']:,} unique LEAP 24-25 students across four FirstLine schools, internal assessment coverage ranges from 26% (MAP Math) to 99% (course grades).</p>

<table>
<thead><tr>
<th>System</th><th>Subject</th><th>Window</th><th>n Matched</th><th>Coverage</th>
</tr></thead>
<tbody>"""

coverage_rows = [
    ('anet', 'ELA', 'BOY', 'anet ELA BOY'),
    ('anet', 'ELA', 'MOY', 'anet ELA MOY'),
    ('anet', 'ELA', 'EOY', 'anet ELA EOY'),
    ('anet', 'Math', 'BOY', 'anet Math BOY'),
    ('anet', 'Math', 'MOY', 'anet Math MOY'),
    ('anet', 'Math', 'EOY', 'anet Math EOY'),
    ('MAP', 'ELA', 'BOY', 'MAP ELA BOY'),
    ('MAP', 'Math', 'BOY', 'MAP Math BOY'),
    ('Grades', 'ELA', 'Y1', 'Grade ELA Y1'),
    ('Grades', 'Math', 'Y1', 'Grade Math Y1'),
]

for sys, subj, window, key in coverage_rows:
    cv = R['coverage'].get(key, {})
    n = cv.get('n', 0)
    p = cv.get('pct', 0)
    css = ' class="bad"' if p < 50 else (' class="muted"' if p < 80 else '')
    html += f"<tr><td class='label'>{sys}</td><td class='label'>{subj}</td><td class='label'>{window}</td><td>{n:,}</td><td{css}>{p:.1f}%</td></tr>\n"

html += """</tbody></table>

<div class="finding warning">
<strong>MAP Math BOY covers only 26.4% of LEAP students (499 of 1,887).</strong>
All MAP Math concordance results must be interpreted with extreme caution. MAP ELA coverage is excellent at 92.9%.
</div>

<h2>2. Which Assessment Best Predicts LEAP?</h2>

<h3>Correlation with LEAP Scale Scores</h3>
<p>Pearson r between each internal measure and LEAP scale score. Higher = better predictor. Bar length proportional to r.</p>

<table>
<thead><tr><th>Predictor</th><th>r</th><th>n</th><th></th></tr></thead>
<tbody>"""

# Sort by r descending
sorted_corr = sorted([c for c in corr_data if c.get('r')], key=lambda x: abs(x['r']), reverse=True)
for c in sorted_corr:
    r_val = c['r']
    n_val = c['n']
    bar_w = abs(r_val) * 300
    color = 'var(--green)' if r_val > 0.65 else ('var(--amber)' if r_val > 0.5 else 'var(--red)')
    label = c['label'].replace(' > ', ' &rarr; ')
    css_class = ' class="good"' if r_val > 0.7 else (' class="bad"' if r_val < 0.5 else '')
    n_warn = ' *' if n_val < 600 else ''
    html += f"""<tr>
<td class="label">{label}</td>
<td{css_class}>{r_val:.3f}</td>
<td class="muted">{n_val:,}{n_warn}</td>
<td><div class="bar-container"><div class="bar" style="width:{bar_w:.0f}px;background:{color}"></div></div></td>
</tr>\n"""

html += """</tbody></table>
<p class="muted" style="font-size:0.8rem;">* n < 600 indicates limited sample. MAP Math BOY has only 499 students.</p>

<div class="finding">
<strong>MAP percentile is the strongest per-student predictor &mdash; but only where it has coverage.</strong>
MAP Math %ile &rarr; LEAP Math: r=0.840 (n=499). For practical use at scale, anet Math MOY is the best predictor with adequate coverage: r=0.724 (n=1,700).
Course grades are the weakest predictor: Math r=0.396, ELA r=0.564.
</div>

<h2>3. Concordance: Do Internal Assessments and LEAP Agree on Proficiency?</h2>

<p>A student is &ldquo;proficient&rdquo; on LEAP if they score Mastery or Advanced. For each internal system, we find the threshold that maximizes agreement (concordance rate) with LEAP proficiency.</p>

<table>
<thead><tr>
<th>System</th><th>Threshold</th><th>Concordance</th><th>Kappa</th>
<th>Sensitivity</th><th>Specificity</th><th>PPV</th><th>NPV</th><th>n</th>
</tr></thead>
<tbody>"""

# Sort system summary by kappa descending
sorted_ss = sorted(ss, key=lambda x: x.get('kappa', 0), reverse=True)
for s in sorted_ss:
    k = s.get('kappa', 0)
    kappa_class = ' class="good"' if k > 0.5 else (' class="bad"' if k < 0.35 else '')
    conc_class = ' class="good"' if s['concordance'] > 0.83 else (' class="bad"' if s['concordance'] < 0.78 else '')
    n_warn = ' *' if s['n_conc'] < 600 else ''
    html += f"""<tr>
<td class="label">{s['system']}</td>
<td>{s['threshold']}</td>
<td{conc_class}>{pct(s['concordance'])}</td>
<td{kappa_class}>{num(k)}</td>
<td>{pct(s.get('sensitivity'))}</td>
<td>{pct(s.get('specificity'))}</td>
<td>{pct(s.get('ppv'))}</td>
<td>{pct(s.get('npv'))}</td>
<td class="muted">{s['n_conc']:,}{n_warn}</td>
</tr>\n"""

html += """</tbody></table>

<p class="muted" style="font-size:0.8rem;">
Concordance = (TP+TN)/Total. Kappa = chance-corrected agreement. Sensitivity = % of LEAP-proficient students correctly identified.
Specificity = % of LEAP-not-proficient students correctly identified. PPV = % of flagged-proficient who are LEAP-proficient.
NPV = % of flagged-not-proficient who are LEAP-not-proficient.
</p>

<div class="finding">
<strong>To achieve even 77% concordance, grades must be set at 90% (A-).</strong>
The optimal grade threshold for predicting LEAP proficiency is an A-. Below that, grades over-identify proficiency. This confirms massive grade inflation: a B in math class tells you almost nothing about whether a student will be proficient on LEAP.
</div>

<h3>2&times;2 Concordance Matrices: Best Internal Predictors vs. Worst</h3>
<div class="grid-2">"""

# Show anet EOY ELA and Grade ELA side by side
for s in sorted_ss:
    if s['system'] == 'anet ELA EOY':
        anet_ela_s = s
    if s['system'] == 'Grade ELA':
        grade_ela_s = s
    if s['system'] == 'anet Math EOY':
        anet_math_s = s
    if s['system'] == 'Grade Math':
        grade_math_s = s

def matrix_card(s, title):
    total = s['tp'] + s['fp'] + s['fn'] + s['tn']
    return f"""<div class="card">
<h3>{title}</h3>
<p class="muted" style="font-size:0.8rem;">Threshold: {s['threshold']} | n={s['n_conc']:,}</p>
<div class="matrix">
  <div class="cell header"></div>
  <div class="cell header">LEAP Prof.</div>
  <div class="cell header">LEAP Not Prof.</div>
  <div class="cell header">Internal Prof.</div>
  <div class="cell tp"><strong>{s['tp']}</strong><br><span style="font-size:0.75rem;color:var(--green)">True Pos</span></div>
  <div class="cell fp"><strong>{s['fp']}</strong><br><span style="font-size:0.75rem;color:var(--amber)">False Pos</span></div>
  <div class="cell header">Internal Not Prof.</div>
  <div class="cell fn"><strong>{s['fn']}</strong><br><span style="font-size:0.75rem;color:var(--rose)">False Neg</span></div>
  <div class="cell tn"><strong>{s['tn']}</strong><br><span style="font-size:0.75rem;color:var(--blue)">True Neg</span></div>
</div>
<div class="stat-row">
  <div class="stat"><span class="value">{pct(s['concordance'])}</span><span class="label">Concordance</span></div>
  <div class="stat"><span class="value">{num(s['kappa'])}</span><span class="label">Kappa</span></div>
  <div class="stat"><span class="value">{pct(s['sensitivity'])}</span><span class="label">Sensitivity</span></div>
  <div class="stat"><span class="value">{pct(s['specificity'])}</span><span class="label">Specificity</span></div>
</div>
</div>"""

html += matrix_card(anet_ela_s, "anet ELA EOY vs LEAP ELA")
html += matrix_card(grade_ela_s, "Grade ELA (Y1) vs LEAP ELA")
html += matrix_card(anet_math_s, "anet Math EOY vs LEAP Math")
html += matrix_card(grade_math_s, "Grade Math (Y1) vs LEAP Math")

html += """</div>

<h2>4. The Blind Spots: High Grades, Low LEAP</h2>

<div class="finding critical">
<strong>451 students (24.2%) earn a B or better in Math but score Unsatisfactory or Approaching Basic on LEAP.</strong>
In ELA, 234 students (12.6%) have the same mismatch. These students and families receive a false signal of proficiency from report cards.
</div>

<h3>Grade Inflation Rate by School</h3>
<p>Percentage of graded students who earn B+ (&#8805;80%) but score U or AB on LEAP.</p>

<table>
<thead><tr><th>School</th><th>ELA Inflated</th><th>ELA n</th><th>ELA Rate</th><th>Math Inflated</th><th>Math n</th><th>Math Rate</th></tr></thead>
<tbody>"""

school_blind = {
    'Ashe': {'ela': 61, 'ela_n': 529, 'math': 153, 'math_n': 528},
    'Green': {'ela': 26, 'ela_n': 328, 'math': 67, 'math_n': 330},
    'LHA': {'ela': 110, 'ela_n': 511, 'math': 145, 'math_n': 514},
    'Wheatley': {'ela': 37, 'ela_n': 494, 'math': 86, 'math_n': 495},
}

for school in ['Ashe', 'Green', 'LHA', 'Wheatley']:
    b = school_blind[school]
    ela_rate = 100 * b['ela'] / b['ela_n']
    math_rate = 100 * b['math'] / b['math_n']
    ela_css = ' class="bad"' if ela_rate > 15 else ''
    math_css = ' class="bad"' if math_rate > 25 else ''
    html += f"""<tr>
<td class="label">{school}</td>
<td>{b['ela']}</td><td class="muted">{b['ela_n']}</td><td{ela_css}>{ela_rate:.1f}%</td>
<td>{b['math']}</td><td class="muted">{b['math_n']}</td><td{math_css}>{math_rate:.1f}%</td>
</tr>\n"""

html += f"""<tr style="font-weight:600;border-top:2px solid var(--border)">
<td class="label">Network</td>
<td>{R['blind_ela_count']}</td><td class="muted">1,862</td><td>{100*R['blind_ela_count']/1862:.1f}%</td>
<td>{R['blind_math_count']}</td><td class="muted">1,867</td><td class="bad">{100*R['blind_math_count']/1867:.1f}%</td>
</tr>
</tbody></table>

<h3>Math Grade Inflation Heatmap: School &times; Grade</h3>
<p>Percentage of students with Math grade B+ but LEAP Math U/AB. Darker = more inflated.</p>

<table class="heatmap">
<thead><tr><th>School</th><th>G3</th><th>G4</th><th>G5</th><th>G6</th><th>G7</th><th>G8</th></tr></thead>
<tbody>"""

def heat_class(rate):
    if rate < 10: return 'heat-0'
    if rate < 20: return 'heat-1'
    if rate < 35: return 'heat-2'
    if rate < 50: return 'heat-3'
    return 'heat-4'

# Build heatmap from blind_detail
heat_data = {}
for d in bd:
    key = (d['school'], d['grade'])
    heat_data[key] = d

for school in ['Ashe', 'Green', 'LHA', 'Wheatley']:
    html += f"<tr><td class='label'>{school}</td>"
    for g in range(3, 9):
        d = heat_data.get((school, g), {})
        rate = d.get('math_rate', 0)
        n = d.get('math_graded', 0)
        cls = heat_class(rate)
        html += f"<td class='{cls}'>{rate:.0f}%<br><span style='font-size:0.7rem;opacity:0.7'>n={n}</span></td>"
    html += "</tr>\n"

html += """</tbody></table>

<div class="finding critical">
<strong>Grade 6 Math is the inflation epicenter.</strong>
Wheatley G6: 60% inflated (n=84). Ashe G6: 57% (n=92). LHA G4 is an outlier at 57% (n=81).
These grade-school combinations represent the biggest disconnects between classroom assessment and state standards.
</div>

<h3>When anet and Grades Disagree, Who Is Right?</h3>

<table>
<thead><tr><th>Scenario</th><th>ELA</th><th>Math</th></tr></thead>
<tbody>
<tr>
<td class="label">Students with anet &lt;30% but Grade &ge;80% (B)</td>
<td>202</td>
<td>339</td>
</tr>
<tr>
<td class="label">Of those, scored U/AB on LEAP (anet was right)</td>
<td class="bad">122 (60.4%)</td>
<td class="bad">246 (72.6%)</td>
</tr>
<tr>
<td class="label">Triple misalignment (Grade B+, anet &lt;30%, LEAP U/AB)</td>
<td>122</td>
<td>246</td>
</tr>
</tbody>
</table>

<div class="finding">
<strong>When anet flags a student as at-risk but their grade says otherwise, anet is right 60&ndash;73% of the time.</strong>
In Math, nearly 3 out of 4 students in this disagreement zone end up scoring Unsatisfactory or Approaching Basic on LEAP. The grade was a false positive.
</div>

<h2>5. School-Level Concordance Variation</h2>

<p>Does one school&rsquo;s grading align better with LEAP than another&rsquo;s?</p>

<table>
<thead><tr>
<th>School</th>
<th colspan="2">anet ELA EOY</th>
<th colspan="2">anet Math EOY</th>
<th colspan="2">Grade ELA</th>
<th colspan="2">Grade Math</th>
</tr>
<tr>
<th></th>
<th>Conc.</th><th>&kappa;</th>
<th>Conc.</th><th>&kappa;</th>
<th>Conc.</th><th>&kappa;</th>
<th>Conc.</th><th>&kappa;</th>
</tr></thead>
<tbody>"""

for school in ['Ashe', 'Green', 'LHA', 'Wheatley']:
    d = sc[school]
    html += f"<tr><td class='label'>{school}</td>"
    for key in ['anet_ela', 'anet_math', 'grade_ela', 'grade_math']:
        v = d[key]
        conc = v.get('concordance', 0)
        kap = v.get('kappa', 0)
        conc_css = ' class="good"' if conc > 0.83 else (' class="bad"' if conc < 0.7 else '')
        kap_css = ' class="good"' if kap > 0.5 else (' class="bad"' if kap < 0.2 else '')
        html += f"<td{conc_css}>{pct(conc)}</td><td{kap_css}>{num(kap)}</td>"
    html += "</tr>\n"

html += """</tbody></table>

<div class="finding warning">
<strong>Ashe Math grades have near-zero agreement with LEAP (kappa=0.063).</strong>
This is barely above chance. Ashe Math course grades carry almost no information about LEAP readiness. By contrast, Green Math grades show modest alignment (kappa=0.191).
</div>

<h3>School-Level Correlations</h3>
<table>
<thead><tr><th>School</th><th>anet ELA EOY</th><th>anet Math EOY</th><th>MAP ELA %ile</th><th>Grade ELA</th><th>Grade Math</th></tr></thead>
<tbody>"""

for school in ['Ashe', 'Green', 'LHA', 'Wheatley']:
    html += f"<tr><td class='label'>{school}</td>"
    for label in ['anet ELA EOY', 'anet Math EOY', 'MAP ELA %ile', 'Grade ELA', 'Grade Math']:
        v = R['school_corrs'][school].get(label, {})
        r_val = v.get('r')
        n_val = v.get('n', 0)
        if r_val is not None:
            css = ' class="good"' if r_val > 0.7 else (' class="bad"' if r_val < 0.4 else '')
            html += f"<td{css}>{r_val:.3f}<br><span class='muted' style='font-size:0.75rem'>n={n_val}</span></td>"
        else:
            html += "<td class='muted'>&mdash;</td>"
    html += "</tr>\n"

html += """</tbody></table>

<div class="finding critical">
<strong>Ashe Math grades: r=0.147 with LEAP Math scores.</strong>
This is the lowest correlation of any system at any school. A student&rsquo;s Math course grade at Ashe explains only 2% of the variance in their LEAP Math performance. At Green, the same metric explains 48% (r=0.695).
</div>

<h2>6. What Do Grades Actually Measure?</h2>

<h3>Mean Score by LEAP Achievement Level</h3>
<p>If assessments are well-calibrated, scores should increase monotonically across LEAP levels with large separation.</p>

<table>
<thead><tr><th>LEAP Level</th><th>anet EOY ELA</th><th>anet EOY Math</th><th>Grade ELA</th><th>Grade Math</th></tr></thead>
<tbody>"""

# Five-level data from analysis output
anet_ela_levels = {
    'Unsatisfactory': (23.2, 12.0, 301),
    'Approaching Basic': (30.7, 15.1, 460),
    'Basic': (43.9, 16.8, 539),
    'Mastery': (60.1, 18.1, 462),
    'Advanced': (73.9, 13.9, 58),
}
anet_math_levels = {
    'Unsatisfactory': (23.4, 10.8, 382),
    'Approaching Basic': (29.5, 14.1, 579),
    'Basic': (42.5, 18.1, 482),
    'Mastery': (61.3, 17.5, 324),
    'Advanced': (76.6, 16.6, 25),
}
grade_ela_levels = {
    'Unsatisfactory': (72.9, 9.0, 306),
    'Approaching Basic': (76.7, 8.3, 471),
    'Basic': (80.7, 7.0, 551),
    'Mastery': (86.3, 6.3, 475),
    'Advanced': (90.6, 5.7, 59),
}
grade_math_levels = {
    'Unsatisfactory': (75.5, 9.7, 396),
    'Approaching Basic': (79.8, 8.4, 597),
    'Basic': (85.1, 7.4, 505),
    'Mastery': (87.4, 14.4, 344),
    'Advanced': (89.4, 19.0, 25),
}

for level in ['Unsatisfactory', 'Approaching Basic', 'Basic', 'Mastery', 'Advanced']:
    ae = anet_ela_levels[level]
    am = anet_math_levels[level]
    ge = grade_ela_levels[level]
    gm = grade_math_levels[level]
    html += f"""<tr>
<td class="label">{level}</td>
<td>{ae[0]:.1f}% <span class="muted">(&plusmn;{ae[1]:.0f})</span></td>
<td>{am[0]:.1f}% <span class="muted">(&plusmn;{am[1]:.0f})</span></td>
<td>{ge[0]:.1f}% <span class="muted">(&plusmn;{ge[1]:.0f})</span></td>
<td>{gm[0]:.1f}% <span class="muted">(&plusmn;{gm[1]:.0f})</span></td>
</tr>\n"""

# Compute spread
anet_ela_spread = anet_ela_levels['Advanced'][0] - anet_ela_levels['Unsatisfactory'][0]
anet_math_spread = anet_math_levels['Advanced'][0] - anet_math_levels['Unsatisfactory'][0]
grade_ela_spread = grade_ela_levels['Advanced'][0] - grade_ela_levels['Unsatisfactory'][0]
grade_math_spread = grade_math_levels['Advanced'][0] - grade_math_levels['Unsatisfactory'][0]

html += f"""<tr style="font-weight:600;border-top:2px solid var(--border)">
<td class="label">Spread (Adv - Unsat)</td>
<td class="good">{anet_ela_spread:.1f} pp</td>
<td class="good">{anet_math_spread:.1f} pp</td>
<td class="bad">{grade_ela_spread:.1f} pp</td>
<td class="bad">{grade_math_spread:.1f} pp</td>
</tr>
</tbody></table>

<div class="finding">
<strong>anet separates LEAP levels by 50+ percentage points. Grades separate them by only 14&ndash;18 points.</strong>
An Unsatisfactory student averages 23% on anet EOY vs 74% for Advanced (51pp spread). On course grades, the same comparison is 73% vs 91% (18pp) in ELA and 76% vs 89% (14pp) in Math.
Grades compress all performance into a narrow band, making it impossible to distinguish struggling students from thriving ones.
</div>

<h2>7. Scatter Plots: Internal Scores vs LEAP</h2>

<div class="grid-2">
<div class="scatter-container">
<h3>anet ELA EOY (%) vs LEAP ELA Scale Score</h3>
<canvas id="scatter1" width="540" height="400"></canvas>
<div class="tooltip" id="tip1"></div>
<div class="legend">
  <span><span class="dot" style="background:#dc2626"></span> Unsatisfactory</span>
  <span><span class="dot" style="background:#f59e0b"></span> Approaching Basic</span>
  <span><span class="dot" style="background:#3b82f6"></span> Basic</span>
  <span><span class="dot" style="background:#10b981"></span> Mastery</span>
  <span><span class="dot" style="background:#8b5cf6"></span> Advanced</span>
</div>
</div>

<div class="scatter-container">
<h3>Grade ELA Y1 (%) vs LEAP ELA Scale Score</h3>
<canvas id="scatter2" width="540" height="400"></canvas>
<div class="tooltip" id="tip2"></div>
<div class="legend">
  <span><span class="dot" style="background:#dc2626"></span> Unsatisfactory</span>
  <span><span class="dot" style="background:#f59e0b"></span> Approaching Basic</span>
  <span><span class="dot" style="background:#3b82f6"></span> Basic</span>
  <span><span class="dot" style="background:#10b981"></span> Mastery</span>
  <span><span class="dot" style="background:#8b5cf6"></span> Advanced</span>
</div>
</div>

<div class="scatter-container">
<h3>anet Math EOY (%) vs LEAP Math Scale Score</h3>
<canvas id="scatter3" width="540" height="400"></canvas>
<div class="tooltip" id="tip3"></div>
<div class="legend">
  <span><span class="dot" style="background:#dc2626"></span> Unsatisfactory</span>
  <span><span class="dot" style="background:#f59e0b"></span> Approaching Basic</span>
  <span><span class="dot" style="background:#3b82f6"></span> Basic</span>
  <span><span class="dot" style="background:#10b981"></span> Mastery</span>
  <span><span class="dot" style="background:#8b5cf6"></span> Advanced</span>
</div>
</div>

<div class="scatter-container">
<h3>Grade Math Y1 (%) vs LEAP Math Scale Score</h3>
<canvas id="scatter4" width="540" height="400"></canvas>
<div class="tooltip" id="tip4"></div>
<div class="legend">
  <span><span class="dot" style="background:#dc2626"></span> Unsatisfactory</span>
  <span><span class="dot" style="background:#f59e0b"></span> Approaching Basic</span>
  <span><span class="dot" style="background:#3b82f6"></span> Basic</span>
  <span><span class="dot" style="background:#10b981"></span> Mastery</span>
  <span><span class="dot" style="background:#8b5cf6"></span> Advanced</span>
</div>
</div>
</div>

<h2>8. Recommendations</h2>

<div class="finding">
<strong>1. Use anet interims as the primary early-warning system.</strong>
anet BOY/MOY scores at scale (n>1,700) have concordance rates of 78&ndash;86% with LEAP and correlations of 0.58&ndash;0.72. These are the most actionable predictors available network-wide.
</div>

<div class="finding warning">
<strong>2. Investigate Math grading practices, starting with Ashe and Grade 6 network-wide.</strong>
Ashe Math grades have near-zero correlation with LEAP (r=0.147). Grade 6 Math inflation exceeds 50% at two schools. This requires a grading policy review, not just a data fix.
</div>

<div class="finding">
<strong>3. Expand MAP Math BOY administration.</strong>
MAP Math has the highest per-student predictive power (r=0.84) but covers only 26% of students. Expanding coverage to all LEAP-tested students would provide a powerful second signal.
</div>

<div class="finding">
<strong>4. Create a composite risk flag.</strong>
Students flagged by anet &lt;30% AND Grade &ge;80% represent the highest-confidence intervention targets: 73% of them score U/AB on LEAP. Currently 339 students are in this Math blind spot.
</div>

<p class="muted" style="margin-top: 2rem; font-size: 0.8rem;">
Analysis: Eli Vance | Data: BigQuery fls-data-warehouse (LEAP, anet, MAP, grades, roster) | Year: 2024-25 |
{R['n_students']:,} unique LEAP students | 85 cross-school duplicates removed | Generated 2026-02-22
</p>

<script>
const ACH_COLORS = {{
  'Unsatisfactory': '#dc2626',
  'Approaching Basic': '#f59e0b',
  'Basic': '#3b82f6',
  'Mastery': '#10b981',
  'Advanced': '#8b5cf6'
}};

function drawScatter(canvasId, tipId, data, xLabel, yLabel, xMin, xMax, yMin, yMax) {{
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const tip = document.getElementById(tipId);
  const W = canvas.width, H = canvas.height;
  const pad = {{top: 20, right: 20, bottom: 45, left: 55}};
  const pw = W - pad.left - pad.right;
  const ph = H - pad.top - pad.bottom;

  function toX(v) {{ return pad.left + (v - xMin) / (xMax - xMin) * pw; }}
  function toY(v) {{ return pad.top + ph - (v - yMin) / (yMax - yMin) * ph; }}

  // Background
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = '#e2ddd5';
  ctx.lineWidth = 0.5;
  for (let x = Math.ceil(xMin/10)*10; x <= xMax; x += 10) {{
    ctx.beginPath();
    ctx.moveTo(toX(x), pad.top);
    ctx.lineTo(toX(x), pad.top + ph);
    ctx.stroke();
  }}
  for (let y = Math.ceil(yMin/20)*20; y <= yMax; y += 20) {{
    ctx.beginPath();
    ctx.moveTo(pad.left, toY(y));
    ctx.lineTo(pad.left + pw, toY(y));
    ctx.stroke();
  }}

  // Axes
  ctx.strokeStyle = '#1a1a1a';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.left, pad.top);
  ctx.lineTo(pad.left, pad.top + ph);
  ctx.lineTo(pad.left + pw, pad.top + ph);
  ctx.stroke();

  // Axis labels
  ctx.fillStyle = '#5a6474';
  ctx.font = '11px "Source Sans 3", sans-serif';
  ctx.textAlign = 'center';
  for (let x = Math.ceil(xMin/10)*10; x <= xMax; x += 10) {{
    ctx.fillText(x, toX(x), pad.top + ph + 16);
  }}
  ctx.textAlign = 'right';
  for (let y = Math.ceil(yMin/20)*20; y <= yMax; y += 20) {{
    ctx.fillText(y, pad.left - 6, toY(y) + 4);
  }}

  // Axis titles
  ctx.fillStyle = '#1a1a1a';
  ctx.font = '12px "Source Sans 3", sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(xLabel, pad.left + pw/2, H - 4);
  ctx.save();
  ctx.translate(14, pad.top + ph/2);
  ctx.rotate(-Math.PI/2);
  ctx.fillText(yLabel, 0, 0);
  ctx.restore();

  // Points
  data.forEach(function(pt) {{
    const x = toX(pt[0]);
    const y = toY(pt[1]);
    const color = ACH_COLORS[pt[2]] || '#999';
    ctx.globalAlpha = 0.45;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }});
  ctx.globalAlpha = 1;

  // Hover
  canvas.addEventListener('mousemove', function(e) {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    let found = null;
    for (let i = data.length - 1; i >= 0; i--) {{
      const px = toX(data[i][0]);
      const py = toY(data[i][1]);
      if (Math.abs(mx - px) < 6 && Math.abs(my - py) < 6) {{
        found = data[i];
        break;
      }}
    }}
    if (found) {{
      tip.style.display = 'block';
      tip.style.left = (e.clientX - canvas.parentElement.getBoundingClientRect().left + 12) + 'px';
      tip.style.top = (e.clientY - canvas.parentElement.getBoundingClientRect().top - 10) + 'px';
      tip.textContent = xLabel.split(' ')[0] + ': ' + found[0] + ' | LEAP: ' + found[1] + ' | ' + found[2] + ' | ' + found[3];
    }} else {{
      tip.style.display = 'none';
    }}
  }});
  canvas.addEventListener('mouseleave', function() {{ tip.style.display = 'none'; }});
}}

const d1 = {scatter_anet_ela_js};
const d2 = {scatter_grade_ela_js};
const d3 = {scatter_anet_math_js};
const d4 = {scatter_grade_math_js};

drawScatter('scatter1', 'tip1', d1, 'anet ELA EOY (%)', 'LEAP ELA Scale Score', 0, 100, 650, 850);
drawScatter('scatter2', 'tip2', d2, 'Grade ELA Y1 (%)', 'LEAP ELA Scale Score', 30, 100, 650, 850);
drawScatter('scatter3', 'tip3', d3, 'anet Math EOY (%)', 'LEAP Math Scale Score', 0, 100, 650, 850);
drawScatter('scatter4', 'tip4', d4, 'Grade Math Y1 (%)', 'LEAP Math Scale Score', 30, 100, 650, 850);
</script>

</body>
</html>"""

outpath = os.path.join(OUTDIR, 'concordance-analysis.html')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML report written to {outpath}")
print(f"File size: {os.path.getsize(outpath):,} bytes")
