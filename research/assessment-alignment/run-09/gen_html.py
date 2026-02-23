#!/usr/bin/env python3
"""
gen_html.py - Generate PM Standards-Level Diagnostic Analysis HTML report.

Loads JSON data from run-09 query results and produces a self-contained
HTML report at standards-diagnostic.html.

Uses only Python standard library (json, collections, statistics, os).
"""

import json
import os
import statistics
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Paths  (Windows-compatible forward slashes)
# ---------------------------------------------------------------------------
BASE_DIR = "C:/Users/sshirey/bigquery-dashboards/research/assessment-alignment/run-09"

Q01_PATH = os.path.join(BASE_DIR, "q01_results.json")
Q04_PATH = os.path.join(BASE_DIR, "q04_results.json")
Q06_PATH = os.path.join(BASE_DIR, "q06_results.json")
Q07_PATH = os.path.join(BASE_DIR, "q07_results.json")
Q08_MATH_PATH = os.path.join(BASE_DIR, "q08_math_results.json")
Q08_ELA_PATH = os.path.join(BASE_DIR, "q08_ela_results.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "standards-diagnostic.html")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(val, default=0.0):
    """Convert a value to float, returning default on None or failure."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    """Convert a value to int, returning default on None or failure."""
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def fmt_r(val):
    """Format a correlation value to 3 decimal places."""
    return f"{safe_float(val):.3f}"


def fmt_pct(val):
    """Format a proportion as a percentage with 1 decimal."""
    return f"{safe_float(val) * 100:.1f}%"


def r_color(val):
    """Return CSS color for a correlation magnitude."""
    v = safe_float(val)
    if v < 0:
        return "#dc2626"
    if v >= 0.6:
        return "#16a34a"
    if v >= 0.4:
        return "#d97706"
    return "#94a3b8"


def r_bg_color(val):
    """Return CSS background color for heatmap cells."""
    v = safe_float(val)
    if v < 0:
        return "rgba(220, 38, 38, 0.15)"
    if v >= 0.5:
        return "rgba(22, 163, 74, 0.15)"
    if v >= 0.35:
        return "rgba(217, 119, 6, 0.12)"
    return "rgba(148, 163, 184, 0.08)"


def r_text_color(val):
    """Return text color for heatmap cells."""
    v = safe_float(val)
    if v < 0:
        return "#dc2626"
    if v >= 0.5:
        return "#16a34a"
    if v >= 0.35:
        return "#d97706"
    return "#94a3b8"


def esc(text):
    """Escape HTML special characters."""
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def median_val(values):
    """Compute median of a list of floats."""
    if not values:
        return 0.0
    return statistics.median(values)


def mean_val(values):
    """Compute mean of a list of floats."""
    if not values:
        return 0.0
    return statistics.mean(values)


# ---------------------------------------------------------------------------
# Subject configuration
# ---------------------------------------------------------------------------

SUBJECT_R_KEY = {
    "Math": "r_math",
    "English": "r_ela",
    "Science": "r_sci",
    "Social Stu": "r_ss",
}

SUBJECT_LABEL = {
    "Math": "Math",
    "English": "ELA",
    "Science": "Science",
    "Social Stu": "Social Studies",
}

SUBJECT_ORDER = ["Math", "English", "Science", "Social Stu"]

# Subscore columns per subject for heatmap (section 5)
HEATMAP_COLS = {
    "English": [
        ("r_ela_ri", "ELA: RI"),
        ("r_ela_rl", "ELA: RL"),
        ("r_ela_vocab", "ELA: Vocab"),
        ("r_ela_read", "ELA: Reading"),
        ("r_ela_write", "ELA: Writing"),
        ("r_sci_invest", "Sci: Investigate"),
        ("r_sci_eval", "Sci: Evaluate"),
        ("r_math_major", "Math: Major"),
    ],
    "Math": [
        ("r_math_major", "Math: Major"),
        ("r_math_addl", "Math: Additional"),
        ("r_math_reason", "Math: Reasoning"),
        ("r_ela_ri", "ELA: RI"),
        ("r_ela_rl", "ELA: RL"),
    ],
    "Science": [
        ("r_sci_invest", "Sci: Investigate"),
        ("r_sci_eval", "Sci: Evaluate"),
        ("r_sci_reason", "Sci: Reasoning"),
        ("r_ela_ri", "ELA: RI"),
        ("r_ela_rl", "ELA: RL"),
        ("r_ss_context", "SS: Context"),
    ],
    "Social Stu": [
        ("r_ss_context", "SS: Context"),
        ("r_ss_sources", "SS: Sources"),
        ("r_ela_ri", "ELA: RI"),
        ("r_ela_rl", "ELA: RL"),
        ("r_sci_invest", "Sci: Investigate"),
    ],
}


# ---------------------------------------------------------------------------
# Deduplication: CCSS/PS math pairs
# ---------------------------------------------------------------------------

def build_ccss_set(records):
    """Build a set of CCSS.Math.Content suffixes present in the dataset."""
    suffixes = set()
    for r in records:
        std = r.get("LA_State_Standard", "")
        if std.startswith("CCSS.Math.Content."):
            suffixes.add(std.replace("CCSS.Math.Content.", ""))
    return suffixes


def is_ps_duplicate(standard, ccss_suffixes):
    """Check if a PS.Math.Content standard is a duplicate of an existing CCSS standard."""
    if not standard.startswith("PS.Math.Content."):
        return False
    suffix = standard.replace("PS.Math.Content.", "")
    return suffix in ccss_suffixes


def dedup_math(records, ccss_suffixes):
    """Remove PS.Math.Content duplicates where CCSS equivalent exists."""
    return [r for r in records if not is_ps_duplicate(r.get("LA_State_Standard", ""), ccss_suffixes)]


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_json(path):
    """Load JSON file, return list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


print("Loading data...")
q01 = load_json(Q01_PATH)
q04 = load_json(Q04_PATH)
q06 = load_json(Q06_PATH)
q07 = load_json(Q07_PATH)
q08_math = load_json(Q08_MATH_PATH)
q08_ela = load_json(Q08_ELA_PATH)

# Build CCSS suffix set from q04 Math records for dedup
all_math_q04 = [r for r in q04 if r["Subject"] == "Math"]
ccss_suffixes = build_ccss_set(all_math_q04)

print(f"  q01: {len(q01)} records")
print(f"  q04: {len(q04)} records")
print(f"  q06: {len(q06)} records")
print(f"  q07: {len(q07)} records")
print(f"  q08_math: {len(q08_math)} records")
print(f"  q08_ela: {len(q08_ela)} records")
print(f"  CCSS/PS overlapping suffixes: {len(ccss_suffixes)}")


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def build_css():
    """Return the complete CSS stylesheet."""
    return """
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..900;1,8..60,300..900&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Sans+3:ital,wght@0,300..900;1,300..900&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Source Serif 4', Georgia, serif;
    background: #faf8f5;
    color: #1a1a1a;
    line-height: 1.65;
    font-size: 16px;
    padding: 2rem 1rem;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
    font-weight: 700;
    color: #1a1a1a;
    line-height: 1.3;
}

h1 { font-size: 2.2rem; margin-bottom: 0.5rem; }
h2 { font-size: 1.6rem; margin: 2.5rem 0 1rem; border-bottom: 2px solid #e2ddd5; padding-bottom: 0.5rem; }
h3 { font-size: 1.25rem; margin: 1.5rem 0 0.75rem; }
h4 { font-size: 1.1rem; margin: 1rem 0 0.5rem; }

p { margin-bottom: 1rem; }

.subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 1.15rem;
    color: #5a6474;
    font-weight: 400;
    font-style: italic;
    margin-bottom: 0.75rem;
}

.datestamp {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #5a6474;
    margin-bottom: 2rem;
}

.summary-bullets {
    list-style: disc;
    padding-left: 1.5rem;
    margin-bottom: 1.5rem;
}
.summary-bullets li {
    margin-bottom: 0.5rem;
    line-height: 1.5;
}
.summary-bullets strong {
    color: #1a1a1a;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0 1.5rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}

thead {
    position: sticky;
    top: 0;
    z-index: 2;
}

th {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    background: #1a1a1a;
    color: #faf8f5;
    padding: 0.6rem 0.75rem;
    text-align: left;
    white-space: nowrap;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #e2ddd5;
    vertical-align: middle;
}

tr:nth-child(even) td {
    background: rgba(226, 221, 213, 0.2);
}

tr:hover td {
    background: rgba(226, 221, 213, 0.45);
}

.r-bar {
    display: inline-block;
    height: 14px;
    border-radius: 2px;
    vertical-align: middle;
    margin-left: 0.4rem;
}

.text-muted {
    color: #5a6474;
}

.text-green { color: #16a34a; }
.text-amber { color: #d97706; }
.text-red { color: #dc2626; }
.text-muted-data { color: #94a3b8; }

/* Callout boxes */
.callout {
    border-left: 4px solid #e2ddd5;
    background: rgba(226, 221, 213, 0.18);
    padding: 1rem 1.25rem;
    margin: 1.25rem 0;
    border-radius: 0 6px 6px 0;
    font-size: 0.95rem;
}

.callout.green {
    border-left-color: #16a34a;
    background: rgba(22, 163, 74, 0.06);
}

.callout.amber {
    border-left-color: #d97706;
    background: rgba(217, 119, 6, 0.06);
}

.callout.red {
    border-left-color: #dc2626;
    background: rgba(220, 38, 38, 0.06);
}

.callout.blue {
    border-left-color: #2563eb;
    background: rgba(37, 99, 235, 0.06);
}

.callout strong {
    font-family: 'Source Sans 3', sans-serif;
}

/* Details / collapsible */
details {
    margin: 1rem 0;
    border: 1px solid #e2ddd5;
    border-radius: 6px;
    overflow: hidden;
}

summary {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    font-size: 1.05rem;
    padding: 0.75rem 1rem;
    cursor: pointer;
    background: rgba(226, 221, 213, 0.2);
    border-bottom: 1px solid #e2ddd5;
    user-select: none;
}

summary:hover {
    background: rgba(226, 221, 213, 0.4);
}

details[open] summary {
    border-bottom: 1px solid #e2ddd5;
}

details > .details-body {
    padding: 1rem;
}

/* Reset table margin inside details */
details .details-body table {
    margin: 0.5rem 0 1rem;
}

/* 2x2 grid */
.quadrant-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin: 1rem 0;
}

.quadrant {
    border-radius: 8px;
    padding: 1rem 1.25rem;
    border: 1px solid #e2ddd5;
}

.quadrant h4 {
    margin: 0 0 0.5rem;
    font-size: 1rem;
}

.quadrant .count {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.quadrant ul {
    list-style: none;
    padding: 0;
    font-size: 0.85rem;
    font-family: 'IBM Plex Mono', monospace;
}

.quadrant ul li {
    margin-bottom: 0.25rem;
    color: #5a6474;
}

.q-invest { background: rgba(22, 163, 74, 0.08); border-color: #16a34a; }
.q-invest .count { color: #16a34a; }
.q-maintain { background: rgba(37, 99, 235, 0.08); border-color: #2563eb; }
.q-maintain .count { color: #2563eb; }
.q-lowpri { background: rgba(217, 119, 6, 0.08); border-color: #d97706; }
.q-lowpri .count { color: #d97706; }
.q-depri { background: rgba(148, 163, 184, 0.08); border-color: #94a3b8; }
.q-depri .count { color: #94a3b8; }

/* Heatmap */
.heatmap-table td {
    text-align: center;
    font-size: 0.8rem;
    padding: 0.4rem 0.5rem;
    font-weight: 500;
}

.heatmap-table td:first-child {
    text-align: left;
    font-size: 0.78rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 240px;
}

/* Gap highlight */
.gap-cell {
    background: rgba(220, 38, 38, 0.12) !important;
    color: #dc2626;
    font-weight: 600;
}

/* Side by side */
.side-by-side {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin: 1rem 0;
}

@media (max-width: 768px) {
    .side-by-side { grid-template-columns: 1fr; }
    .quadrant-grid { grid-template-columns: 1fr; }
    h1 { font-size: 1.6rem; }
}

/* Methodology */
.methodology ul {
    list-style: disc;
    padding-left: 1.5rem;
}
.methodology li {
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
}

/* Section numbers */
.section-num {
    font-family: 'IBM Plex Mono', monospace;
    color: #94a3b8;
    font-weight: 400;
    font-size: 0.85em;
    margin-right: 0.4rem;
}

footer {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 2px solid #e2ddd5;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.85rem;
    color: #5a6474;
    text-align: center;
}
"""


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

# ---- Section 1: Header & Executive Summary ----

def build_header():
    return """
<header>
    <h1>PM Standards-Level Diagnostic Analysis</h1>
    <p class="subtitle">Which specific standards predict LEAP outcomes, and which are instructional dead weight?</p>
    <p class="datestamp">Run 9 of 9 &middot; February 23, 2026 &middot; Analyst: Eli Vance &middot; FirstLine Schools</p>

    <h2><span class="section-num">1</span> Executive Summary</h2>
    <ul class="summary-bullets">
        <li><strong>963 PM standards</strong> correlated with LEAP scale scores across four subjects</li>
        <li><strong>Math strongest predictor:</strong> top r = 0.773 (LA.MA.3.OA.A.3)</li>
        <li><strong>56 CCSS/PS duplicates</strong> identified in Math (PS.Math.Content mirrors CCSS.Math.Content)</li>
        <li><strong>61 Hard + Predictive Math standards</strong> represent the highest-ROI instructional targets</li>
        <li>ELA reading standards show strong cross-subject prediction of LEAP Science subscores</li>
    </ul>
</header>
"""


# ---- Section 2: Standards Taxonomy Summary Table ----

def build_taxonomy_table(q04_data):
    rows = []
    for subj in SUBJECT_ORDER:
        r_key = SUBJECT_R_KEY[subj]
        label = SUBJECT_LABEL[subj]
        subj_rows = [r for r in q04_data if r["Subject"] == subj]

        if subj == "Math":
            subj_rows = dedup_math(subj_rows, ccss_suffixes)

        r_values = [safe_float(r[r_key]) for r in subj_rows]
        pct_values = [safe_float(r["avg_pct_correct"]) for r in subj_rows]

        n_stds = len(subj_rows)
        mean_r = mean_val(r_values) if r_values else 0
        med_r = median_val(r_values) if r_values else 0
        max_r = max(r_values) if r_values else 0
        pct_above_05 = (sum(1 for v in r_values if v >= 0.5) / n_stds * 100) if n_stds else 0
        avg_pct = mean_val(pct_values) if pct_values else 0

        rows.append(f"""
        <tr>
            <td style="font-family: 'Source Sans 3', sans-serif; font-weight: 600;">{esc(label)}</td>
            <td>{n_stds}</td>
            <td>{mean_r:.3f}</td>
            <td>{med_r:.3f}</td>
            <td style="color: {r_color(max_r)}; font-weight: 600;">{max_r:.3f}</td>
            <td>{pct_above_05:.1f}%</td>
            <td>{avg_pct * 100:.1f}%</td>
        </tr>""")

    return f"""
<h2><span class="section-num">2</span> Standards Taxonomy Summary</h2>
<table>
    <thead>
        <tr>
            <th>Subject</th>
            <th># Standards</th>
            <th>Mean r</th>
            <th>Median r</th>
            <th>Max r</th>
            <th>% with r &ge; 0.5</th>
            <th>Avg % Correct</th>
        </tr>
    </thead>
    <tbody>
        {"".join(rows)}
    </tbody>
</table>

<div class="callout green">
    <strong>Key Finding:</strong> Grade 3 Multiplication &amp; Division standards are the 3 strongest LEAP Math
    predictors (r = 0.765&ndash;0.773). These standards deserve maximized instructional time.
</div>
"""


# ---- Section 3: Top 10 / Bottom 10 per Subject ----

def build_top_bottom(q04_data):
    html_parts = []
    html_parts.append('<h2><span class="section-num">3</span> Top 10 &amp; Bottom 10 Standards per Subject</h2>')

    for subj in SUBJECT_ORDER:
        r_key = SUBJECT_R_KEY[subj]
        label = SUBJECT_LABEL[subj]
        subj_rows = [r for r in q04_data if r["Subject"] == subj]

        if subj == "Math":
            subj_rows = dedup_math(subj_rows, ccss_suffixes)

        sorted_desc = sorted(subj_rows, key=lambda r: safe_float(r[r_key]), reverse=True)
        sorted_asc = sorted(subj_rows, key=lambda r: safe_float(r[r_key]))

        top10 = sorted_desc[:10]
        bottom10 = sorted_asc[:10]

        # Top 10 table rows
        top_rows = []
        for row in top10:
            r_val = safe_float(row[r_key])
            r_sq = r_val ** 2
            bar_width = max(0, min(r_val * 100, 100))
            bar_color = r_color(r_val)
            top_rows.append(f"""
            <tr>
                <td style="font-size: 0.8rem; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{esc(row['LA_State_Standard'])}</td>
                <td style="color: {bar_color}; font-weight: 600;">{r_val:.3f}</td>
                <td>{r_sq:.3f}</td>
                <td>{row['n']}</td>
                <td>{fmt_pct(row['avg_pct_correct'])}</td>
                <td style="width: 120px;">
                    <span class="r-bar" style="width: {bar_width}%; background: {bar_color};"></span>
                </td>
            </tr>""")

        # Bottom 10 table rows
        bottom_rows = []
        for row in bottom10:
            r_val = safe_float(row[r_key])
            if r_val < 0:
                interp = "Negative relationship"
            elif r_val < 0.1:
                interp = "Near-zero LEAP payoff"
            elif r_val < 0.2:
                interp = "Negligible predictor"
            elif r_val < 0.3:
                interp = "Very weak predictor"
            else:
                interp = "Weak predictor"
            bottom_rows.append(f"""
            <tr>
                <td style="font-size: 0.8rem; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{esc(row['LA_State_Standard'])}</td>
                <td style="color: {r_color(r_val)};">{r_val:.3f}</td>
                <td>{row['n']}</td>
                <td>{fmt_pct(row['avg_pct_correct'])}</td>
                <td class="text-muted" style="font-family: 'Source Sans 3', sans-serif; font-size: 0.85rem;">{interp}</td>
            </tr>""")

        html_parts.append(f"""
<details>
    <summary>{esc(label)}: Top 10 &amp; Bottom 10 Standards</summary>
    <div class="details-body">
        <h4>Top 10 {esc(label)} Standards (by own-subject LEAP r)</h4>
        <table>
            <thead>
                <tr>
                    <th>Standard</th>
                    <th>r</th>
                    <th>R&sup2;</th>
                    <th>n</th>
                    <th>Avg % Correct</th>
                    <th>r Magnitude</th>
                </tr>
            </thead>
            <tbody>
                {"".join(top_rows)}
            </tbody>
        </table>

        <h4>Bottom 10 {esc(label)} Standards</h4>
        <table>
            <thead>
                <tr>
                    <th>Standard</th>
                    <th>r</th>
                    <th>n</th>
                    <th>Avg %</th>
                    <th>Interpretation</th>
                </tr>
            </thead>
            <tbody>
                {"".join(bottom_rows)}
            </tbody>
        </table>
    </div>
</details>""")

    html_parts.append("""
<div class="callout amber">
    <strong>Watch:</strong> Bottom 10 Math standards have r &lt; 0.10 with LEAP Math. Near-zero LEAP payoff &mdash;
    time spent on these standards does not move the LEAP needle.
</div>
""")
    return "\n".join(html_parts)


# ---- Section 4: Difficulty x Predictive Power (2x2 quadrants) ----

def build_quadrants(q04_data):
    html_parts = []
    html_parts.append('<h2><span class="section-num">4</span> Difficulty &times; Predictive Power</h2>')
    html_parts.append('<p class="text-muted">Standards classified into 4 quadrants: difficulty threshold 50%, predictive threshold r = 0.5</p>')

    for subj in ["Math", "English"]:
        r_key = SUBJECT_R_KEY[subj]
        label = SUBJECT_LABEL[subj]
        subj_rows = [r for r in q04_data if r["Subject"] == subj]

        if subj == "Math":
            subj_rows = dedup_math(subj_rows, ccss_suffixes)

        invest, maintain, lowpri, depri = [], [], [], []

        for row in subj_rows:
            avg_pct = safe_float(row["avg_pct_correct"])
            r_val = safe_float(row[r_key])
            hard = avg_pct < 0.5
            predictive = r_val >= 0.5

            if hard and predictive:
                invest.append(row)
            elif not hard and predictive:
                maintain.append(row)
            elif hard and not predictive:
                lowpri.append(row)
            else:
                depri.append(row)

        # Sort each quadrant by r descending
        for lst in [invest, maintain, lowpri, depri]:
            lst.sort(key=lambda r: safe_float(r[r_key]), reverse=True)

        def quad_top3(lst):
            items = []
            for row in lst[:3]:
                items.append(f"<li>{esc(row['LA_State_Standard'])} (r={safe_float(row[r_key]):.3f})</li>")
            return "".join(items)

        html_parts.append(f"""
<h3>{esc(label)}</h3>
<div class="quadrant-grid">
    <div class="quadrant q-invest">
        <h4>INVEST (Hard + Predictive)</h4>
        <div class="count">{len(invest)}</div>
        <ul>{quad_top3(invest)}</ul>
    </div>
    <div class="quadrant q-maintain">
        <h4>MAINTAIN (Easy + Predictive)</h4>
        <div class="count">{len(maintain)}</div>
        <ul>{quad_top3(maintain)}</ul>
    </div>
    <div class="quadrant q-lowpri">
        <h4>LOW PRIORITY (Hard + Not Predictive)</h4>
        <div class="count">{len(lowpri)}</div>
        <ul>{quad_top3(lowpri)}</ul>
    </div>
    <div class="quadrant q-depri">
        <h4>DEPRIORITIZE (Easy + Not Predictive)</h4>
        <div class="count">{len(depri)}</div>
        <ul>{quad_top3(depri)}</ul>
    </div>
</div>""")

    html_parts.append("""
<div class="callout green">
    <strong>Highest ROI:</strong> 61 Math standards and 36 ELA standards are Hard + Predictive &mdash;
    the highest-ROI instructional targets. These are the standards students struggle with that also
    strongly predict LEAP performance.
</div>
""")
    return "\n".join(html_parts)


# ---- Section 5: PM Standard x LEAP Subscore Heatmap ----

def build_heatmap(q04_data, q06_data):
    html_parts = []
    html_parts.append('<h2><span class="section-num">5</span> PM Standard &times; LEAP Subscore Heatmap</h2>')
    html_parts.append('<p class="text-muted">Top 15 PM standards per subject (by own-subject LEAP scale score r). '
                       'Cell color: r &ge; 0.5 green, 0.35&ndash;0.5 amber, &lt; 0.35 muted, &lt; 0 red.</p>')

    # Index q06 by (Subject, Standard)
    q06_idx = {}
    for row in q06_data:
        key = (row["Subject"], row["LA_State_Standard"])
        q06_idx[key] = row

    for subj in SUBJECT_ORDER:
        r_key = SUBJECT_R_KEY[subj]
        label = SUBJECT_LABEL[subj]
        cols = HEATMAP_COLS[subj]

        subj_q04 = [r for r in q04_data if r["Subject"] == subj]
        if subj == "Math":
            subj_q04 = dedup_math(subj_q04, ccss_suffixes)

        sorted_rows = sorted(subj_q04, key=lambda r: safe_float(r[r_key]), reverse=True)[:15]

        col_headers = "".join(
            f'<th style="font-size: 0.72rem; text-align: center;">{esc(clabel)}</th>'
            for ckey, clabel in cols
        )

        body_rows = []
        for row in sorted_rows:
            std = row["LA_State_Standard"]
            q06_row = q06_idx.get((subj, std), {})
            cells = []
            for ckey, clabel in cols:
                val = safe_float(q06_row.get(ckey))
                bg = r_bg_color(val)
                tc = r_text_color(val)
                cells.append(f'<td style="background: {bg}; color: {tc}; font-weight: 500;">{val:.2f}</td>')
            body_rows.append(f"""
            <tr>
                <td>{esc(std)}</td>
                {"".join(cells)}
            </tr>""")

        html_parts.append(f"""
<details open>
    <summary>{esc(label)} Subscore Heatmap</summary>
    <div class="details-body" style="overflow-x: auto;">
        <table class="heatmap-table">
            <thead>
                <tr>
                    <th style="min-width: 200px;">PM Standard</th>
                    {col_headers}
                </tr>
            </thead>
            <tbody>
                {"".join(body_rows)}
            </tbody>
        </table>
    </div>
</details>""")

    html_parts.append("""
<div class="callout blue">
    <strong>Cross-Subject Signal:</strong> PM ELA reading standards predict LEAP Science subscores at r = 0.40&ndash;0.63.
    Reading comprehension is a gateway skill that lifts performance across disciplines.
</div>
""")
    return "\n".join(html_parts)


# ---- Section 6: School-Level Gaps ----

def build_school_gaps(q04_data, q07_data):
    html_parts = []
    html_parts.append('<h2><span class="section-num">6</span> School-Level Performance Gaps</h2>')
    html_parts.append('<p class="text-muted">For top 5 standards per subject: average % correct by school. '
                       'Cells highlighted red are &gt;10 percentage points below the network weighted mean.</p>')

    schools = ["Ashe", "Green", "LHA", "Wheatley"]

    # Index q07 by (Subject, Standard, School)
    q07_idx = {}
    for row in q07_data:
        key = (row["Subject"], row["LA_State_Standard"], row["School"])
        q07_idx[key] = row

    # Which standards are available in q07 per subject
    q07_stds_by_subj = defaultdict(set)
    for row in q07_data:
        q07_stds_by_subj[row["Subject"]].add(row["LA_State_Standard"])

    for subj in SUBJECT_ORDER:
        r_key = SUBJECT_R_KEY[subj]
        label = SUBJECT_LABEL[subj]

        subj_q04 = [r for r in q04_data if r["Subject"] == subj]
        if subj == "Math":
            subj_q04 = dedup_math(subj_q04, ccss_suffixes)

        available = q07_stds_by_subj.get(subj, set())
        subj_q04_avail = [r for r in subj_q04 if r["LA_State_Standard"] in available]
        top5 = sorted(subj_q04_avail, key=lambda r: safe_float(r[r_key]), reverse=True)[:5]

        if not top5:
            continue

        body_rows = []
        for row in top5:
            std = row["LA_State_Standard"]
            total_n = 0
            total_weighted = 0.0
            school_data = {}
            for sch in schools:
                q07_row = q07_idx.get((subj, std, sch))
                if q07_row:
                    n = safe_int(q07_row["n"])
                    avg = safe_float(q07_row["avg_pct"])
                    school_data[sch] = (avg, n)
                    total_n += n
                    total_weighted += avg * n

            network_avg = total_weighted / total_n if total_n > 0 else 0

            cells = []
            for sch in schools:
                if sch in school_data:
                    avg, n = school_data[sch]
                    diff = avg - network_avg
                    css_class = ' class="gap-cell"' if diff < -0.10 else ""
                    cells.append(f'<td{css_class}>{avg * 100:.1f}%</td>')
                else:
                    cells.append('<td class="text-muted">--</td>')

            cells.append(f'<td style="font-weight: 600;">{network_avg * 100:.1f}%</td>')

            body_rows.append(f"""
            <tr>
                <td style="font-size: 0.8rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{esc(std)}</td>
                {"".join(cells)}
            </tr>""")

        html_parts.append(f"""
<h3>{esc(label)}</h3>
<table>
    <thead>
        <tr>
            <th>Standard</th>
            {"".join(f'<th>{esc(s)}</th>' for s in schools)}
            <th>Network Avg</th>
        </tr>
    </thead>
    <tbody>
        {"".join(body_rows)}
    </tbody>
</table>""")

    html_parts.append("""
<div class="callout red">
    <strong>Gap Alert:</strong> Green scores 43% on LA.MA.3.MD.A.1 vs 48% network average.
    School-level variation reveals where targeted intervention can close gaps.
</div>
""")
    return "\n".join(html_parts)


# ---- Section 7: Cross-Subject Prediction ----

def build_cross_subject(q04_data):
    html_parts = []
    html_parts.append('<h2><span class="section-num">7</span> Cross-Subject Prediction</h2>')
    html_parts.append('<p class="text-muted">PM standards from one subject predicting LEAP scores in a different subject.</p>')

    cross_configs = [
        ("English", "r_math", "English &rarr; LEAP Math", "LEAP Math r"),
        ("English", "r_sci", "English &rarr; LEAP Science", "LEAP Science r"),
        ("Math", "r_ela", "Math &rarr; LEAP ELA", "LEAP ELA r"),
        ("Science", "r_ss", "Science &rarr; LEAP Social Studies", "LEAP Soc.Stu r"),
    ]

    for source_subj, target_key, title, col_label in cross_configs:
        subj_rows = [r for r in q04_data if r["Subject"] == source_subj]
        if source_subj == "Math":
            subj_rows = dedup_math(subj_rows, ccss_suffixes)

        sorted_rows = sorted(subj_rows, key=lambda r: safe_float(r[target_key]), reverse=True)[:5]

        body_rows = []
        for row in sorted_rows:
            r_val = safe_float(row[target_key])
            own_key = SUBJECT_R_KEY[source_subj]
            own_r = safe_float(row[own_key])
            body_rows.append(f"""
            <tr>
                <td style="font-size: 0.8rem;">{esc(row['LA_State_Standard'])}</td>
                <td style="color: {r_color(r_val)}; font-weight: 600;">{r_val:.3f}</td>
                <td>{own_r:.3f}</td>
                <td>{fmt_pct(row['avg_pct_correct'])}</td>
                <td>{row['n']}</td>
            </tr>""")

        html_parts.append(f"""
<h3>{title}</h3>
<table>
    <thead>
        <tr>
            <th>PM Standard</th>
            <th>{col_label}</th>
            <th>Own-Subject r</th>
            <th>Avg % Correct</th>
            <th>n</th>
        </tr>
    </thead>
    <tbody>
        {"".join(body_rows)}
    </tbody>
</table>""")

    html_parts.append("""
<div class="callout green">
    <strong>Master Skill:</strong> PM ELA W.8.2 predicts LEAP Math at r = 0.715 &mdash;
    reading is the master skill. Strong ELA performance lifts all boats.
</div>
""")
    return "\n".join(html_parts)


# ---- Section 8: Student Weakness Profiles ----

def build_weakness_profiles(q08_math_data, q08_ela_data):
    html_parts = []
    html_parts.append('<h2><span class="section-num">8</span> Student Weakness Profiles</h2>')
    html_parts.append('<p class="text-muted">Distribution of weakness counts '
                       '(standards where student scores below 50% correct) per student.</p>')

    def weakness_dist(data):
        dist = Counter()
        for row in data:
            wc = safe_int(row["weak_count"])
            dist[wc] += 1
        return dist

    math_dist = weakness_dist(q08_math_data)
    ela_dist = weakness_dist(q08_ela_data)

    all_counts = sorted(set(list(math_dist.keys()) + list(ela_dist.keys())))
    total_math = sum(math_dist.values())
    total_ela = sum(ela_dist.values())

    # Summary stats
    math_weak = sum(v for k, v in math_dist.items() if k > 0)
    ela_weak = sum(v for k, v in ela_dist.items() if k > 0)
    math_weak_students = [r for r in q08_math_data if safe_int(r["weak_count"]) > 0]
    ela_weak_students = [r for r in q08_ela_data if safe_int(r["weak_count"]) > 0]
    math_avg_pct = mean_val([safe_float(r["avg_pct"]) for r in math_weak_students]) if math_weak_students else 0
    ela_avg_pct = mean_val([safe_float(r["avg_pct"]) for r in ela_weak_students]) if ela_weak_students else 0

    html_parts.append(f"""
<div class="side-by-side">
    <div>
        <h4>Math</h4>
        <p class="text-muted" style="font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;">
            {total_math} students tested &middot; {math_weak} with &ge; 1 weakness ({math_weak / total_math * 100:.1f}%)
            &middot; Avg pct among weak: {math_avg_pct * 100:.1f}%
        </p>
    </div>
    <div>
        <h4>ELA</h4>
        <p class="text-muted" style="font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;">
            {total_ela} students tested &middot; {ela_weak} with &ge; 1 weakness ({ela_weak / total_ela * 100:.1f}%)
            &middot; Avg pct among weak: {ela_avg_pct * 100:.1f}%
        </p>
    </div>
</div>
""")

    rows = []
    for wc in all_counts:
        m_n = math_dist.get(wc, 0)
        e_n = ela_dist.get(wc, 0)
        m_pct = (m_n / total_math * 100) if total_math else 0
        e_pct = (e_n / total_ela * 100) if total_ela else 0

        # Bar widths (scaled so 60% = max bar width for visual clarity)
        m_bar_w = min(m_pct * 2, 120)
        e_bar_w = min(e_pct * 2, 120)

        rows.append(f"""
        <tr>
            <td style="font-weight: 600;">{wc}</td>
            <td>{m_n}</td>
            <td>
                {m_pct:.1f}%
                <span class="r-bar" style="width: {m_bar_w:.0f}px; background: #2563eb;"></span>
            </td>
            <td>{e_n}</td>
            <td>
                {e_pct:.1f}%
                <span class="r-bar" style="width: {e_bar_w:.0f}px; background: #16a34a;"></span>
            </td>
        </tr>""")

    html_parts.append(f"""
<table>
    <thead>
        <tr>
            <th>Weak Count</th>
            <th>Math n</th>
            <th>Math %</th>
            <th>ELA n</th>
            <th>ELA %</th>
        </tr>
    </thead>
    <tbody>
        {"".join(rows)}
    </tbody>
</table>
""")
    return "\n".join(html_parts)


# ---- Section 9: Methodology Notes ----

def build_methodology():
    return """
<h2><span class="section-num">9</span> Methodology Notes</h2>
<div class="methodology">
    <ul>
        <li><strong>Data source:</strong> Progress Monitoring (PM) item-level responses from PowerSchool Performance Matters,
            linked to LEAP 2025 scale scores and subscores via State Student Number.</li>
        <li><strong>Correlation method:</strong> Pearson product-moment correlation between student-level PM percent correct
            on each standard and LEAP scale scores / subscores.</li>
        <li><strong>Minimum sample:</strong> Standards required n &ge; 50 matched students to be included in correlation analysis.</li>
        <li><strong>Deduplication:</strong> 56 PS.Math.Content standards are exact mirrors of CCSS.Math.Content standards.
            Where both exist, the PS version is excluded to avoid double-counting.</li>
        <li><strong>Quadrant thresholds:</strong> Difficulty &lt; 50% average correct = &ldquo;hard&rdquo;; r &ge; 0.5 = &ldquo;predictive&rdquo;.
            These thresholds were chosen based on distributional breakpoints.</li>
        <li><strong>School-level gaps:</strong> Weighted network average computed from individual school n-counts.
            Cells flagged when &gt;10 percentage points below network mean.</li>
        <li><strong>Weakness profiles:</strong> A student is &ldquo;weak&rdquo; on a standard if their average percent correct &lt; 50%.
            Only standards tested for each student are counted.</li>
        <li><strong>Caveat:</strong> Correlations reflect association, not causation. PM item quality, curricular alignment,
            and timing of assessments may influence observed relationships.</li>
        <li><strong>Enrichment subject:</strong> Excluded from analysis due to insufficient sample size (n = 2 standards with correlations).</li>
    </ul>
</div>
"""


# ---- Footer ----

def build_footer():
    return """
<footer>
    <p>PM Standards-Level Diagnostic Analysis &middot; Run 9 of 9 &middot; February 2026</p>
    <p>FirstLine Schools &middot; Analyst: Eli Vance &middot; Generated programmatically from BigQuery exports</p>
</footer>
"""


# ---------------------------------------------------------------------------
# Assemble full HTML document
# ---------------------------------------------------------------------------

def build_html():
    css = build_css()
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>PM Standards-Level Diagnostic Analysis</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        '<div class="container">',
        build_header(),
        build_taxonomy_table(q04),
        build_top_bottom(q04),
        build_quadrants(q04),
        build_heatmap(q04, q06),
        build_school_gaps(q04, q07),
        build_cross_subject(q04),
        build_weakness_profiles(q08_math, q08_ela),
        build_methodology(),
        build_footer(),
        "</div>",
        "</body>",
        "</html>",
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating HTML report...")
    html = build_html()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"Report written to: {OUTPUT_PATH}")
    print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print("Done.")
