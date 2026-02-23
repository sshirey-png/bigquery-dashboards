#!/usr/bin/env python3
"""
Run 4: Concordance Analysis
Joins LEAP 24-25 to internal assessments (anet, MAP, grades).
Computes concordance matrices, correlations, blind spots.
Generates self-contained HTML report.
"""

import json
import math
import os
import sys

OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# DATA LOADING
# ============================================================

def load_json(path):
    with open(path) as f:
        return json.load(f)

def safe_float(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except:
        return None

def safe_int(v):
    if v is None or v == '':
        return None
    try:
        return int(v)
    except:
        return None

def normalize_school(s):
    if not s:
        return None
    s = s.strip()
    if 'Hughes' in s:
        return 'LHA'
    if 'Green' in s:
        return 'Green'
    if 'Ashe' in s:
        return 'Ashe'
    if 'Wheatley' in s:
        return 'Wheatley'
    return s

print("Loading data...")
master = load_json(os.path.join(OUTDIR, 'master_extract.json'))
grades_data = load_json(os.path.join(OUTDIR, 'grades_extract.json'))

# Build grades lookup
grades_by_lasid = {}
for r in grades_data:
    if r.get('LASID'):
        grades_by_lasid[r['LASID']] = r

# Join grades to master
for r in master:
    g = grades_by_lasid.get(r.get('LASID'), {})
    r['ela_grade_pct'] = g.get('ela_pct')
    r['ela_grade_letter'] = g.get('ela_letter')
    r['math_grade_pct'] = g.get('math_pct')
    r['math_grade_letter'] = g.get('math_letter')
    r['school_short'] = normalize_school(r.get('school'))
    r['grade_int'] = safe_int(r.get('grade'))

# Deduplicate by LASID
seen = set()
deduped = []
for r in master:
    lid = r.get('LASID')
    if lid and lid not in seen:
        seen.add(lid)
        deduped.append(r)
dup_count = len(master) - len(deduped)
master = deduped
print(f"Loaded {len(master)} unique LEAP students ({dup_count} duplicates removed)")

# Coverage stats
coverage = {}
fields_to_check = {
    'anet_ela_boy': 'anet ELA BOY',
    'anet_ela_moy': 'anet ELA MOY',
    'anet_ela_eoy': 'anet ELA EOY',
    'anet_math_boy': 'anet Math BOY',
    'anet_math_moy': 'anet Math MOY',
    'anet_math_eoy': 'anet Math EOY',
    'map_ela_pctile': 'MAP ELA BOY',
    'map_math_pctile': 'MAP Math BOY',
    'ela_grade_pct': 'Grade ELA Y1',
    'math_grade_pct': 'Grade Math Y1',
}
for field, label in fields_to_check.items():
    n = sum(1 for r in master if safe_float(r.get(field)) is not None)
    coverage[label] = {'n': n, 'pct': 100 * n / len(master)}
    print(f"  {label}: {n}/{len(master)} ({coverage[label]['pct']:.1f}%)")

# ============================================================
# CONCORDANCE ANALYSIS
# ============================================================

def is_leap_proficient(ach):
    return ach in ('Mastery', 'Advanced')

def concordance_2x2(data, internal_field, threshold, subject='ela', filter_fn=None):
    """
    Returns: tp, fp, fn, tn, stats_dict
    LEAP proficient = Mastery/Advanced
    Internal proficient = score >= threshold
    """
    leap_field = f'leap_{subject}_ach'
    tp = fp = fn = tn = 0
    for r in data:
        if filter_fn and not filter_fn(r):
            continue
        leap_val = (r.get(leap_field) or '').strip()
        int_val = safe_float(r.get(internal_field))
        if not leap_val or int_val is None:
            continue
        leap_prof = is_leap_proficient(leap_val)
        int_prof = int_val >= threshold
        if int_prof and leap_prof:
            tp += 1
        elif int_prof and not leap_prof:
            fp += 1
        elif not int_prof and leap_prof:
            fn += 1
        else:
            tn += 1
    total = tp + fp + fn + tn
    if total == 0:
        return tp, fp, fn, tn, {}
    concordance = (tp + tn) / total
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (total * total) if total > 0 else 0
    kappa = (concordance - pe) / (1 - pe) if pe < 1 else 0
    return tp, fp, fn, tn, {
        'n': total, 'concordance': concordance,
        'sensitivity': sensitivity, 'specificity': specificity,
        'ppv': ppv, 'npv': npv, 'kappa': kappa
    }

def concordance_map_proj(data, subject='ela', filter_fn=None):
    """Concordance using MAP projected proficiency level vs LEAP actual."""
    leap_field = f'leap_{subject}_ach'
    proj_field = f'map_{subject}_proj'
    tp = fp = fn = tn = 0
    for r in data:
        if filter_fn and not filter_fn(r):
            continue
        leap_val = (r.get(leap_field) or '').strip()
        proj_val = (r.get(proj_field) or '').strip()
        if not leap_val or not proj_val:
            continue
        leap_prof = is_leap_proficient(leap_val)
        proj_prof = proj_val in ('Mastery', 'Advanced')
        if proj_prof and leap_prof:
            tp += 1
        elif proj_prof and not leap_prof:
            fp += 1
        elif not proj_prof and leap_prof:
            fn += 1
        else:
            tn += 1
    total = tp + fp + fn + tn
    if total == 0:
        return tp, fp, fn, tn, {}
    concordance = (tp + tn) / total
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (total * total) if total > 0 else 0
    kappa = (concordance - pe) / (1 - pe) if pe < 1 else 0
    return tp, fp, fn, tn, {
        'n': total, 'concordance': concordance,
        'sensitivity': sensitivity, 'specificity': specificity,
        'ppv': ppv, 'npv': npv, 'kappa': kappa
    }

def pearson_r(x_vals, y_vals):
    n = len(x_vals)
    if n < 3:
        return None
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    ss_xx = sum((x - mean_x) ** 2 for x in x_vals)
    ss_yy = sum((y - mean_y) ** 2 for y in y_vals)
    denom = math.sqrt(ss_xx * ss_yy)
    if denom == 0:
        return None
    return ss_xy / denom

def compute_corr(data, fx, fy, filter_fn=None):
    pairs = []
    for r in data:
        if filter_fn and not filter_fn(r):
            continue
        x = safe_float(r.get(fx))
        y = safe_float(r.get(fy))
        if x is not None and y is not None:
            pairs.append((x, y))
    if len(pairs) < 3:
        return None, 0
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    return pearson_r(xs, ys), len(pairs)

# ============================================================
# 1. THRESHOLD OPTIMIZATION FOR ANET
# ============================================================

print("\n=== ANET THRESHOLD OPTIMIZATION ===")
thresholds = list(range(25, 66, 5))

anet_fields = {
    'anet_ela_boy': ('ela', 'anet ELA BOY'),
    'anet_ela_moy': ('ela', 'anet ELA MOY'),
    'anet_ela_eoy': ('ela', 'anet ELA EOY'),
    'anet_math_boy': ('math', 'anet Math BOY'),
    'anet_math_moy': ('math', 'anet Math MOY'),
    'anet_math_eoy': ('math', 'anet Math EOY'),
}

threshold_results = {}
for field, (subj, label) in anet_fields.items():
    results = []
    for t in thresholds:
        tp, fp, fn, tn, stats = concordance_2x2(master, field, t, subj)
        if stats:
            stats['threshold'] = t
            stats['tp'] = tp
            stats['fp'] = fp
            stats['fn'] = fn
            stats['tn'] = tn
            results.append(stats)
    threshold_results[label] = results
    # Find max concordance
    if results:
        best = max(results, key=lambda x: x['concordance'])
        print(f"  {label}: best threshold={best['threshold']}%, concordance={best['concordance']:.1%}, kappa={best['kappa']:.3f} (n={best['n']})")

# ============================================================
# 2. CONCORDANCE AT OPTIMAL THRESHOLDS
# ============================================================

print("\n=== CONCORDANCE AT OPTIMAL THRESHOLDS ===")

# Optimal thresholds (choosing based on max concordance)
optimal_thresholds = {}
for label, results in threshold_results.items():
    if results:
        best = max(results, key=lambda x: x['concordance'])
        optimal_thresholds[label] = best['threshold']

# Also compute concordance for MAP projected proficiency and grades
print("\n--- MAP Projected Proficiency ---")
map_ela_tp, map_ela_fp, map_ela_fn, map_ela_tn, map_ela_stats = concordance_map_proj(master, 'ela')
print(f"  MAP ELA proj: concordance={map_ela_stats.get('concordance',0):.1%}, kappa={map_ela_stats.get('kappa',0):.3f} (n={map_ela_stats.get('n',0)})")
map_math_tp, map_math_fp, map_math_fn, map_math_tn, map_math_stats = concordance_map_proj(master, 'math')
print(f"  MAP Math proj: concordance={map_math_stats.get('concordance',0):.1%}, kappa={map_math_stats.get('kappa',0):.3f} (n={map_math_stats.get('n',0)})")

# MAP percentile thresholds
print("\n--- MAP Percentile Thresholds ---")
map_pctile_results = {}
for subj_label, subj, field in [('MAP ELA %ile', 'ela', 'map_ela_pctile'), ('MAP Math %ile', 'math', 'map_math_pctile')]:
    results = []
    for t in [25, 30, 35, 40, 45, 50, 55, 60]:
        tp, fp, fn, tn, stats = concordance_2x2(master, field, t, subj)
        if stats:
            stats['threshold'] = t
            stats['tp'] = tp
            stats['fp'] = fp
            stats['fn'] = fn
            stats['tn'] = tn
            results.append(stats)
    map_pctile_results[subj_label] = results
    if results:
        best = max(results, key=lambda x: x['concordance'])
        print(f"  {subj_label}: best threshold={best['threshold']}th, concordance={best['concordance']:.1%}, kappa={best['kappa']:.3f} (n={best['n']})")

# Grade thresholds
print("\n--- Grade Thresholds ---")
grade_results = {}
for subj_label, subj, field in [('Grade ELA', 'ela', 'ela_grade_pct'), ('Grade Math', 'math', 'math_grade_pct')]:
    results = []
    for t in [60, 65, 70, 75, 80, 85, 90]:
        tp, fp, fn, tn, stats = concordance_2x2(master, field, t, subj)
        if stats:
            stats['threshold'] = t
            stats['tp'] = tp
            stats['fp'] = fp
            stats['fn'] = fn
            stats['tn'] = tn
            results.append(stats)
    grade_results[subj_label] = results
    if results:
        best = max(results, key=lambda x: x['concordance'])
        print(f"  {subj_label}: best threshold={best['threshold']}%, concordance={best['concordance']:.1%}, kappa={best['kappa']:.3f} (n={best['n']})")

# ============================================================
# 3. CORRELATIONS
# ============================================================

print("\n=== CORRELATIONS WITH LEAP SCALE SCORES ===")

corr_pairs = [
    ('anet_ela_boy', 'leap_ela_ss', 'anet ELA BOY > LEAP ELA'),
    ('anet_ela_moy', 'leap_ela_ss', 'anet ELA MOY > LEAP ELA'),
    ('anet_ela_eoy', 'leap_ela_ss', 'anet ELA EOY > LEAP ELA'),
    ('anet_math_boy', 'leap_math_ss', 'anet Math BOY > LEAP Math'),
    ('anet_math_moy', 'leap_math_ss', 'anet Math MOY > LEAP Math'),
    ('anet_math_eoy', 'leap_math_ss', 'anet Math EOY > LEAP Math'),
    ('map_ela_pctile', 'leap_ela_ss', 'MAP ELA pctile > LEAP ELA'),
    ('map_ela_rit', 'leap_ela_ss', 'MAP ELA RIT > LEAP ELA'),
    ('map_math_pctile', 'leap_math_ss', 'MAP Math pctile > LEAP Math'),
    ('map_math_rit', 'leap_math_ss', 'MAP Math RIT > LEAP Math'),
    ('ela_grade_pct', 'leap_ela_ss', 'Grade ELA > LEAP ELA'),
    ('math_grade_pct', 'leap_math_ss', 'Grade Math > LEAP Math'),
]

corr_results = []
for fx, fy, label in corr_pairs:
    r, n = compute_corr(master, fx, fy)
    corr_results.append({'label': label, 'r': r, 'n': n})
    if r is not None:
        print(f"  {label}: r={r:.3f} (n={n})")
    else:
        print(f"  {label}: insufficient data (n={n})")

# School-level correlations
print("\n=== SCHOOL-LEVEL CORRELATIONS ===")
schools = ['Ashe', 'Green', 'LHA', 'Wheatley']
school_corrs = {}
key_pairs = [
    ('anet_ela_eoy', 'leap_ela_ss', 'anet ELA EOY'),
    ('anet_math_eoy', 'leap_math_ss', 'anet Math EOY'),
    ('map_ela_pctile', 'leap_ela_ss', 'MAP ELA %ile'),
    ('ela_grade_pct', 'leap_ela_ss', 'Grade ELA'),
    ('math_grade_pct', 'leap_math_ss', 'Grade Math'),
]
for school in schools:
    school_corrs[school] = {}
    filt = lambda r, s=school: r.get('school_short') == s
    for fx, fy, label in key_pairs:
        r, n = compute_corr(master, fx, fy, filter_fn=filt)
        school_corrs[school][label] = {'r': r, 'n': n}
        if r is not None:
            print(f"  {school} | {label}: r={r:.3f} (n={n})")

# ============================================================
# 4. SCHOOL-LEVEL CONCORDANCE
# ============================================================

print("\n=== SCHOOL-LEVEL CONCORDANCE ===")
# Use anet EOY as primary, at optimal threshold
school_concordance = {}
for school in schools:
    filt = lambda r, s=school: r.get('school_short') == s
    school_concordance[school] = {}

    # anet ELA EOY
    opt_t = optimal_thresholds.get('anet ELA EOY', 50)
    tp, fp, fn, tn, stats = concordance_2x2(master, 'anet_ela_eoy', opt_t, 'ela', filt)
    school_concordance[school]['anet_ela'] = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, **stats, 'threshold': opt_t}

    # anet Math EOY
    opt_t = optimal_thresholds.get('anet Math EOY', 50)
    tp, fp, fn, tn, stats = concordance_2x2(master, 'anet_math_eoy', opt_t, 'math', filt)
    school_concordance[school]['anet_math'] = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, **stats, 'threshold': opt_t}

    # Grade ELA
    tp, fp, fn, tn, stats = concordance_2x2(master, 'ela_grade_pct', 80, 'ela', filt)
    school_concordance[school]['grade_ela'] = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, **stats, 'threshold': 80}

    # Grade Math
    tp, fp, fn, tn, stats = concordance_2x2(master, 'math_grade_pct', 80, 'math', filt)
    school_concordance[school]['grade_math'] = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, **stats, 'threshold': 80}

    print(f"  {school}:")
    for k, v in school_concordance[school].items():
        if 'concordance' in v:
            print(f"    {k}: concordance={v['concordance']:.1%}, kappa={v['kappa']:.3f} (n={v['n']})")

# ============================================================
# 5. BLIND SPOTS
# ============================================================

print("\n=== BLIND SPOT ANALYSIS ===")

# Grade inflation: Grade >= 80 (B) but LEAP Unsatisfactory or Approaching Basic
blind_ela = []
blind_math = []
for r in master:
    ela_g = safe_float(r.get('ela_grade_pct'))
    math_g = safe_float(r.get('math_grade_pct'))
    ela_ach = (r.get('leap_ela_ach') or '').strip()
    math_ach = (r.get('leap_math_ach') or '').strip()

    if ela_g is not None and ela_g >= 80 and ela_ach in ('Unsatisfactory', 'Approaching Basic'):
        blind_ela.append(r)
    if math_g is not None and math_g >= 80 and math_ach in ('Unsatisfactory', 'Approaching Basic'):
        blind_math.append(r)

print(f"  ELA Grade Inflation: {len(blind_ela)} students with B+ grade but U/AB on LEAP")
print(f"  Math Grade Inflation: {len(blind_math)} students with B+ grade but U/AB on LEAP")

# Breakdown by school
for school in schools:
    n_ela = sum(1 for r in blind_ela if r.get('school_short') == school)
    n_math = sum(1 for r in blind_math if r.get('school_short') == school)
    # Total students with grades at this school
    total_ela_graded = sum(1 for r in master if r.get('school_short') == school and safe_float(r.get('ela_grade_pct')) is not None)
    total_math_graded = sum(1 for r in master if r.get('school_short') == school and safe_float(r.get('math_grade_pct')) is not None)
    print(f"  {school}: ELA={n_ela}/{total_ela_graded} ({100*n_ela/max(total_ela_graded,1):.1f}%), Math={n_math}/{total_math_graded} ({100*n_math/max(total_math_graded,1):.1f}%)")

# Breakdown by grade
print("\n  By grade:")
for g in range(3, 9):
    n_ela = sum(1 for r in blind_ela if r.get('grade_int') == g)
    n_math = sum(1 for r in blind_math if r.get('grade_int') == g)
    total_g = sum(1 for r in master if r.get('grade_int') == g)
    print(f"    Grade {g}: ELA blind={n_ela}, Math blind={n_math} (of {total_g} LEAP students)")

# Students where anet says at-risk but grades say fine
anet_risk_grade_ok_ela = []
anet_risk_grade_ok_math = []
for r in master:
    anet_e = safe_float(r.get('anet_ela_eoy'))
    anet_m = safe_float(r.get('anet_math_eoy'))
    ela_g = safe_float(r.get('ela_grade_pct'))
    math_g = safe_float(r.get('math_grade_pct'))

    if anet_e is not None and anet_e < 30 and ela_g is not None and ela_g >= 80:
        anet_risk_grade_ok_ela.append(r)
    if anet_m is not None and anet_m < 30 and math_g is not None and math_g >= 80:
        anet_risk_grade_ok_math.append(r)

print(f"\n  anet <30% but Grade >=80%:")
print(f"    ELA: {len(anet_risk_grade_ok_ela)} students")
print(f"    Math: {len(anet_risk_grade_ok_math)} students")

# What % of these anet-flagged students actually scored U/AB on LEAP?
for label, group, subj in [('ELA', anet_risk_grade_ok_ela, 'ela'), ('Math', anet_risk_grade_ok_math, 'math')]:
    total = len(group)
    if total == 0:
        continue
    u_ab = sum(1 for r in group if (r.get(f'leap_{subj}_ach') or '').strip() in ('Unsatisfactory', 'Approaching Basic'))
    print(f"    {label}: {u_ab}/{total} ({100*u_ab/total:.1f}%) scored U/AB on LEAP (anet was right, grade was wrong)")

# Triple disagreement: high grade, low anet, low LEAP
print("\n  Triple misalignment (Grade B+, anet <30%, LEAP U/AB):")
triple_ela = [r for r in anet_risk_grade_ok_ela if (r.get('leap_ela_ach') or '').strip() in ('Unsatisfactory', 'Approaching Basic')]
triple_math = [r for r in anet_risk_grade_ok_math if (r.get('leap_math_ach') or '').strip() in ('Unsatisfactory', 'Approaching Basic')]
print(f"    ELA: {len(triple_ela)} students")
print(f"    Math: {len(triple_math)} students")

for school in schools:
    n_e = sum(1 for r in triple_ela if r.get('school_short') == school)
    n_m = sum(1 for r in triple_math if r.get('school_short') == school)
    print(f"      {school}: ELA={n_e}, Math={n_m}")

# ============================================================
# 6. SYSTEM COMPARISON SUMMARY
# ============================================================

print("\n=== SYSTEM COMPARISON SUMMARY ===")

# For each system, use optimal threshold and report concordance + correlation
system_summary = []

# anet BOY ELA
for label, field, subj, ss_field in [
    ('anet ELA BOY', 'anet_ela_boy', 'ela', 'leap_ela_ss'),
    ('anet ELA MOY', 'anet_ela_moy', 'ela', 'leap_ela_ss'),
    ('anet ELA EOY', 'anet_ela_eoy', 'ela', 'leap_ela_ss'),
    ('anet Math BOY', 'anet_math_boy', 'math', 'leap_math_ss'),
    ('anet Math MOY', 'anet_math_moy', 'math', 'leap_math_ss'),
    ('anet Math EOY', 'anet_math_eoy', 'math', 'leap_math_ss'),
]:
    tr = threshold_results.get(label, [])
    if tr:
        best = max(tr, key=lambda x: x['concordance'])
        r_val, n_r = compute_corr(master, field, ss_field)
        system_summary.append({
            'system': label,
            'threshold': f"{best['threshold']}%",
            'concordance': best['concordance'],
            'kappa': best['kappa'],
            'sensitivity': best['sensitivity'],
            'specificity': best['specificity'],
            'ppv': best['ppv'],
            'npv': best['npv'],
            'r': r_val,
            'n_conc': best['n'],
            'n_corr': n_r,
            'tp': best['tp'],
            'fp': best['fp'],
            'fn': best['fn'],
            'tn': best['tn'],
        })

# MAP projected proficiency
for label, stats, subj, ss_field, pctile_field in [
    ('MAP ELA proj', map_ela_stats, 'ela', 'leap_ela_ss', 'map_ela_pctile'),
    ('MAP Math proj', map_math_stats, 'math', 'leap_math_ss', 'map_math_pctile'),
]:
    if stats:
        r_val, n_r = compute_corr(master, pctile_field, ss_field)
        tp_v = map_ela_tp if 'ELA' in label else map_math_tp
        fp_v = map_ela_fp if 'ELA' in label else map_math_fp
        fn_v = map_ela_fn if 'ELA' in label else map_math_fn
        tn_v = map_ela_tn if 'ELA' in label else map_math_tn
        system_summary.append({
            'system': label,
            'threshold': 'M/A proj',
            'concordance': stats['concordance'],
            'kappa': stats['kappa'],
            'sensitivity': stats['sensitivity'],
            'specificity': stats['specificity'],
            'ppv': stats['ppv'],
            'npv': stats['npv'],
            'r': r_val,
            'n_conc': stats['n'],
            'n_corr': n_r,
            'tp': tp_v,
            'fp': fp_v,
            'fn': fn_v,
            'tn': tn_v,
        })

# MAP percentile at optimal threshold
for label, results, subj, ss_field in [
    ('MAP ELA %ile', map_pctile_results.get('MAP ELA %ile', []), 'ela', 'leap_ela_ss'),
    ('MAP Math %ile', map_pctile_results.get('MAP Math %ile', []), 'math', 'leap_math_ss'),
]:
    if results:
        best = max(results, key=lambda x: x['concordance'])
        pctile_field = 'map_ela_pctile' if 'ELA' in label else 'map_math_pctile'
        r_val, n_r = compute_corr(master, pctile_field, ss_field)
        system_summary.append({
            'system': label,
            'threshold': f"{best['threshold']}th",
            'concordance': best['concordance'],
            'kappa': best['kappa'],
            'sensitivity': best['sensitivity'],
            'specificity': best['specificity'],
            'ppv': best['ppv'],
            'npv': best['npv'],
            'r': r_val,
            'n_conc': best['n'],
            'n_corr': n_r,
            'tp': best['tp'],
            'fp': best['fp'],
            'fn': best['fn'],
            'tn': best['tn'],
        })

# Grades
for label, results, subj, ss_field in [
    ('Grade ELA', grade_results.get('Grade ELA', []), 'ela', 'leap_ela_ss'),
    ('Grade Math', grade_results.get('Grade Math', []), 'math', 'leap_math_ss'),
]:
    if results:
        best = max(results, key=lambda x: x['concordance'])
        grade_field = 'ela_grade_pct' if 'ELA' in label else 'math_grade_pct'
        r_val, n_r = compute_corr(master, grade_field, ss_field)
        system_summary.append({
            'system': label,
            'threshold': f"{best['threshold']}%",
            'concordance': best['concordance'],
            'kappa': best['kappa'],
            'sensitivity': best['sensitivity'],
            'specificity': best['specificity'],
            'ppv': best['ppv'],
            'npv': best['npv'],
            'r': r_val,
            'n_conc': best['n'],
            'n_corr': n_r,
            'tp': best['tp'],
            'fp': best['fp'],
            'fn': best['fn'],
            'tn': best['tn'],
        })

for s in system_summary:
    r_str = f"{s['r']:.3f}" if s.get('r') else 'N/A'
    print(f"  {s['system']}: conc={s['concordance']:.1%}, kappa={s['kappa']:.3f}, r={r_str} (n_conc={s['n_conc']}, n_corr={s['n_corr']})")

# ============================================================
# 7. SCATTER DATA FOR CHARTS
# ============================================================

# Prepare scatter data for key relationships
def get_scatter_data(data, fx, fy, filter_fn=None, max_pts=2000):
    pts = []
    for r in data:
        if filter_fn and not filter_fn(r):
            continue
        x = safe_float(r.get(fx))
        y = safe_float(r.get(fy))
        if x is not None and y is not None:
            leap_ach = (r.get('leap_ela_ach') or r.get('leap_math_ach') or '').strip()
            pts.append({
                'x': round(x, 1),
                'y': int(y) if y == int(y) else round(y, 1),
                'school': r.get('school_short', ''),
                'grade': r.get('grade_int', ''),
                'ach': leap_ach,
            })
    return pts[:max_pts]

scatter_anet_ela = get_scatter_data(master, 'anet_ela_eoy', 'leap_ela_ss')
scatter_anet_math = get_scatter_data(master, 'anet_math_eoy', 'leap_math_ss')
scatter_map_ela = get_scatter_data(master, 'map_ela_pctile', 'leap_ela_ss')
scatter_grade_ela = get_scatter_data(master, 'ela_grade_pct', 'leap_ela_ss')
scatter_grade_math = get_scatter_data(master, 'math_grade_pct', 'leap_math_ss')

# ============================================================
# 8. GRADE-LEVEL BLIND SPOT DETAIL
# ============================================================

print("\n=== GRADE-LEVEL BLIND SPOT DETAIL ===")
blind_detail = []
for g in range(3, 9):
    for school in schools:
        filt = lambda r, g2=g, s=school: r.get('grade_int') == g2 and r.get('school_short') == s
        total = sum(1 for r in master if filt(r))
        if total == 0:
            continue

        # Math grade inflation
        math_inflated = sum(1 for r in master if filt(r)
                          and safe_float(r.get('math_grade_pct')) is not None
                          and safe_float(r.get('math_grade_pct')) >= 80
                          and (r.get('leap_math_ach') or '').strip() in ('Unsatisfactory', 'Approaching Basic'))
        math_graded = sum(1 for r in master if filt(r) and safe_float(r.get('math_grade_pct')) is not None)

        # ELA grade inflation
        ela_inflated = sum(1 for r in master if filt(r)
                         and safe_float(r.get('ela_grade_pct')) is not None
                         and safe_float(r.get('ela_grade_pct')) >= 80
                         and (r.get('leap_ela_ach') or '').strip() in ('Unsatisfactory', 'Approaching Basic'))
        ela_graded = sum(1 for r in master if filt(r) and safe_float(r.get('ela_grade_pct')) is not None)

        if math_graded > 0 or ela_graded > 0:
            blind_detail.append({
                'grade': g,
                'school': school,
                'n': total,
                'math_inflated': math_inflated,
                'math_graded': math_graded,
                'math_rate': 100 * math_inflated / max(math_graded, 1),
                'ela_inflated': ela_inflated,
                'ela_graded': ela_graded,
                'ela_rate': 100 * ela_inflated / max(ela_graded, 1),
            })
            if math_inflated > 0 or ela_inflated > 0:
                print(f"  G{g} {school}: Math={math_inflated}/{math_graded} ({100*math_inflated/max(math_graded,1):.0f}%), ELA={ela_inflated}/{ela_graded} ({100*ela_inflated/max(ela_graded,1):.0f}%)")

# ============================================================
# 9. FIVE-LEVEL CONCORDANCE (full achievement level mapping)
# ============================================================

print("\n=== FIVE-LEVEL CONCORDANCE ===")

ach_levels = ['Unsatisfactory', 'Approaching Basic', 'Basic', 'Mastery', 'Advanced']

# anet EOY score by LEAP level
print("\nanet EOY % by LEAP ELA level:")
for level in ach_levels:
    vals = [safe_float(r.get('anet_ela_eoy')) for r in master
            if (r.get('leap_ela_ach') or '').strip() == level and safe_float(r.get('anet_ela_eoy')) is not None]
    if vals:
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mean)**2 for v in vals) / len(vals)) if len(vals) > 1 else 0
        print(f"  {level}: mean={mean:.1f}%, sd={sd:.1f}%, n={len(vals)}")

print("\nanet EOY % by LEAP Math level:")
for level in ach_levels:
    vals = [safe_float(r.get('anet_math_eoy')) for r in master
            if (r.get('leap_math_ach') or '').strip() == level and safe_float(r.get('anet_math_eoy')) is not None]
    if vals:
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mean)**2 for v in vals) / len(vals)) if len(vals) > 1 else 0
        print(f"  {level}: mean={mean:.1f}%, sd={sd:.1f}%, n={len(vals)}")

# Grade % by LEAP level
print("\nGrade ELA % by LEAP ELA level:")
for level in ach_levels:
    vals = [safe_float(r.get('ela_grade_pct')) for r in master
            if (r.get('leap_ela_ach') or '').strip() == level and safe_float(r.get('ela_grade_pct')) is not None]
    if vals:
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mean)**2 for v in vals) / len(vals)) if len(vals) > 1 else 0
        print(f"  {level}: mean={mean:.1f}%, sd={sd:.1f}%, n={len(vals)}")

print("\nGrade Math % by LEAP Math level:")
for level in ach_levels:
    vals = [safe_float(r.get('math_grade_pct')) for r in master
            if (r.get('leap_math_ach') or '').strip() == level and safe_float(r.get('math_grade_pct')) is not None]
    if vals:
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mean)**2 for v in vals) / len(vals)) if len(vals) > 1 else 0
        print(f"  {level}: mean={mean:.1f}%, sd={sd:.1f}%, n={len(vals)}")

# ============================================================
# SAVE INTERMEDIATE RESULTS FOR HTML GENERATION
# ============================================================

results = {
    'n_students': len(master),
    'n_duplicates': dup_count,
    'coverage': coverage,
    'system_summary': system_summary,
    'threshold_results': threshold_results,
    'map_pctile_results': map_pctile_results,
    'grade_results': grade_results,
    'corr_results': corr_results,
    'school_corrs': school_corrs,
    'school_concordance': school_concordance,
    'blind_ela_count': len(blind_ela),
    'blind_math_count': len(blind_math),
    'blind_detail': blind_detail,
    'triple_ela_count': len(triple_ela),
    'triple_math_count': len(triple_math),
    'anet_risk_grade_ok_ela_count': len(anet_risk_grade_ok_ela),
    'anet_risk_grade_ok_math_count': len(anet_risk_grade_ok_math),
    'scatter_anet_ela': scatter_anet_ela,
    'scatter_anet_math': scatter_anet_math,
    'scatter_map_ela': scatter_map_ela,
    'scatter_grade_ela': scatter_grade_ela,
    'scatter_grade_math': scatter_grade_math,
    'optimal_thresholds': optimal_thresholds,
}

with open(os.path.join(OUTDIR, 'analysis_results.json'), 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== Analysis complete. Results saved to analysis_results.json ===")
