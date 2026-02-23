import json, statistics, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'leap_24_25_raw.json')) as f:
    data_2425 = json.load(f)
with open(os.path.join(BASE, 'leap_23_24_raw.json')) as f:
    data_2324 = json.load(f)

# Normalize grades
for r in data_2324:
    r['Grade'] = str(int(r['Grade'])) if r['Grade'].strip() else r['Grade']
for r in data_2425:
    r['Grade'] = str(int(r['Grade'])) if r['Grade'].strip() else r['Grade']

def short_school(s):
    if 'Ashe' in s: return 'Ashe'
    if 'Green' in s: return 'Green'
    if 'Hughes' in s: return 'LHA'
    if 'Wheatley' in s: return 'Wheatley'
    return s

for r in data_2425 + data_2324:
    r['school_short'] = short_school(r.get('school',''))

ordered_levels = ['Unsatisfactory', 'Approaching Basic', 'Basic', 'Mastery', 'Advanced']

def compute_dist(records, subject_key):
    valid = [r for r in records if (r.get(subject_key) or '').strip() in ordered_levels]
    total = len(valid)
    if total == 0:
        return None
    counts = defaultdict(int)
    for r in valid:
        counts[r[subject_key]] += 1
    result = {'n': total}
    for lev in ordered_levels:
        result[lev] = counts[lev]
        result[lev + '_pct'] = round(100 * counts[lev] / total, 1)
    result['proficient_n'] = counts['Mastery'] + counts['Advanced']
    result['proficient_pct'] = round(100 * (counts['Mastery'] + counts['Advanced']) / total, 1)
    return result

subjects = [
    ('ela_level', 'ELA'),
    ('math_level', 'Math'),
    ('sci_level', 'Science'),
    ('soc_level', 'Social Studies')
]

schools = ['Ashe', 'Green', 'LHA', 'Wheatley']
grades = ['3','4','5','6','7','8']

# ============================================================
# 1. Network-level by subject, both years
# ============================================================
print("=" * 80)
print("NETWORK-LEVEL PROFICIENCY BY SUBJECT")
print("=" * 80)
for subj_key, subj_name in subjects:
    d24 = compute_dist(data_2425, subj_key)
    d23 = compute_dist(data_2324, subj_key)
    if d24 and d23:
        delta = d24['proficient_pct'] - d23['proficient_pct']
        print(f"\n{subj_name}:")
        print(f"  23-24: {d23['proficient_pct']}% proficient (n={d23['n']})")
        print(f"  24-25: {d24['proficient_pct']}% proficient (n={d24['n']})")
        print(f"  Change: {delta:+.1f} pp")
        print(f"  24-25 dist: U={d24['Unsatisfactory_pct']}% AB={d24['Approaching Basic_pct']}% B={d24['Basic_pct']}% M={d24['Mastery_pct']}% A={d24['Advanced_pct']}%")

# ============================================================
# 2. By school, both years
# ============================================================
print("\n" + "=" * 80)
print("PROFICIENCY BY SCHOOL AND SUBJECT (24-25 vs 23-24)")
print("=" * 80)
for sch in schools:
    sch_24 = [r for r in data_2425 if r['school_short'] == sch]
    sch_23 = [r for r in data_2324 if r['school_short'] == sch]
    print(f"\n{sch} (n 24-25={len(sch_24)}, n 23-24={len(sch_23)}):")
    for subj_key, subj_name in subjects:
        d24 = compute_dist(sch_24, subj_key)
        d23 = compute_dist(sch_23, subj_key)
        if d24 and d23:
            delta = d24['proficient_pct'] - d23['proficient_pct']
            print(f"  {subj_name}: {d23['proficient_pct']}% -> {d24['proficient_pct']}% ({delta:+.1f} pp) [n: {d23['n']}->{d24['n']}]")

# ============================================================
# 3. By school and grade, 24-25 (detailed)
# ============================================================
print("\n" + "=" * 80)
print("24-25 PROFICIENCY BY SCHOOL, GRADE, SUBJECT")
print("=" * 80)
for sch in schools:
    print(f"\n--- {sch} ---")
    for g in grades:
        subset = [r for r in data_2425 if r['school_short'] == sch and r['Grade'] == g]
        if not subset:
            continue
        line = f"  Grade {g} (n={len(subset)}): "
        parts = []
        for subj_key, subj_name in subjects:
            d = compute_dist(subset, subj_key)
            if d:
                parts.append(f"{subj_name}={d['proficient_pct']}%")
        print(line + ', '.join(parts))

# ============================================================
# 4. YoY by grade (to find where performance drops)
# ============================================================
print("\n" + "=" * 80)
print("YOY CHANGE BY GRADE (ELA and Math)")
print("=" * 80)
for g in grades:
    g24 = [r for r in data_2425 if r['Grade'] == g]
    g23 = [r for r in data_2324 if r['Grade'] == g]
    if not g24 or not g23:
        continue
    ela24 = compute_dist(g24, 'ela_level')
    ela23 = compute_dist(g23, 'ela_level')
    math24 = compute_dist(g24, 'math_level')
    math23 = compute_dist(g23, 'math_level')
    if ela24 and ela23 and math24 and math23:
        print(f"  Grade {g}: ELA {ela23['proficient_pct']}%->{ela24['proficient_pct']}% ({ela24['proficient_pct']-ela23['proficient_pct']:+.1f}pp), Math {math23['proficient_pct']}%->{math24['proficient_pct']}% ({math24['proficient_pct']-math23['proficient_pct']:+.1f}pp) [n 23={len(g23)}, 24={len(g24)}]")

# ============================================================
# 5. Full distribution table by school and grade (24-25)
# ============================================================
print("\n" + "=" * 80)
print("24-25 FULL DISTRIBUTION BY SCHOOL/GRADE - ELA")
print("=" * 80)
print(f"{'School':<10} {'Gr':>3} {'n':>4}  {'U%':>5} {'AB%':>5} {'B%':>5} {'M%':>5} {'A%':>5}  {'Prof%':>6}")
for sch in schools:
    for g in grades:
        subset = [r for r in data_2425 if r['school_short'] == sch and r['Grade'] == g]
        if not subset:
            continue
        d = compute_dist(subset, 'ela_level')
        if d:
            print(f"{sch:<10} {g:>3} {d['n']:>4}  {d['Unsatisfactory_pct']:>5.1f} {d['Approaching Basic_pct']:>5.1f} {d['Basic_pct']:>5.1f} {d['Mastery_pct']:>5.1f} {d['Advanced_pct']:>5.1f}  {d['proficient_pct']:>6.1f}")

print("\n" + "=" * 80)
print("24-25 FULL DISTRIBUTION BY SCHOOL/GRADE - MATH")
print("=" * 80)
print(f"{'School':<10} {'Gr':>3} {'n':>4}  {'U%':>5} {'AB%':>5} {'B%':>5} {'M%':>5} {'A%':>5}  {'Prof%':>6}")
for sch in schools:
    for g in grades:
        subset = [r for r in data_2425 if r['school_short'] == sch and r['Grade'] == g]
        if not subset:
            continue
        d = compute_dist(subset, 'math_level')
        if d:
            print(f"{sch:<10} {g:>3} {d['n']:>4}  {d['Unsatisfactory_pct']:>5.1f} {d['Approaching Basic_pct']:>5.1f} {d['Basic_pct']:>5.1f} {d['Mastery_pct']:>5.1f} {d['Advanced_pct']:>5.1f}  {d['proficient_pct']:>6.1f}")

# ============================================================
# 6. Scale score statistics
# ============================================================
print("\n" + "=" * 80)
print("24-25 MEAN SCALE SCORES BY SCHOOL")
print("=" * 80)
for sch in schools:
    sch_data = [r for r in data_2425 if r['school_short'] == sch]
    print(f"\n{sch} (n={len(sch_data)}):")
    for ss_key, subj_name in [('ela_ss','ELA'), ('math_ss','Math'), ('sci_ss','Science'), ('soc_ss','Social')]:
        scores = [int(r[ss_key]) for r in sch_data if r.get(ss_key) is not None]
        if scores:
            print(f"  {subj_name}: mean={statistics.mean(scores):.0f}, median={statistics.median(scores):.0f}, sd={statistics.stdev(scores):.0f}, n={len(scores)}")

# ============================================================
# Save processed data for HTML generation
# ============================================================
output = {
    'network_2425': {},
    'network_2324': {},
    'by_school_2425': {},
    'by_school_2324': {},
    'by_school_grade_2425': {},
    'by_school_grade_2324': {},
    'by_grade_yoy': {}
}

for subj_key, subj_name in subjects:
    d24 = compute_dist(data_2425, subj_key)
    d23 = compute_dist(data_2324, subj_key)
    if d24: output['network_2425'][subj_name] = d24
    if d23: output['network_2324'][subj_name] = d23

for sch in schools:
    output['by_school_2425'][sch] = {}
    output['by_school_2324'][sch] = {}
    output['by_school_grade_2425'][sch] = {}
    output['by_school_grade_2324'][sch] = {}
    sch_24 = [r for r in data_2425 if r['school_short'] == sch]
    sch_23 = [r for r in data_2324 if r['school_short'] == sch]
    for subj_key, subj_name in subjects:
        d24 = compute_dist(sch_24, subj_key)
        d23 = compute_dist(sch_23, subj_key)
        if d24: output['by_school_2425'][sch][subj_name] = d24
        if d23: output['by_school_2324'][sch][subj_name] = d23
    for g in grades:
        subset24 = [r for r in data_2425 if r['school_short'] == sch and r['Grade'] == g]
        subset23 = [r for r in data_2324 if r['school_short'] == sch and r['Grade'] == g]
        if subset24:
            output['by_school_grade_2425'][sch][g] = {}
            for subj_key, subj_name in subjects:
                d = compute_dist(subset24, subj_key)
                if d: output['by_school_grade_2425'][sch][g][subj_name] = d
        if subset23:
            output['by_school_grade_2324'][sch][g] = {}
            for subj_key, subj_name in subjects:
                d = compute_dist(subset23, subj_key)
                if d: output['by_school_grade_2324'][sch][g][subj_name] = d

for g in grades:
    output['by_grade_yoy'][g] = {}
    g24 = [r for r in data_2425 if r['Grade'] == g]
    g23 = [r for r in data_2324 if r['Grade'] == g]
    for subj_key, subj_name in subjects:
        d24 = compute_dist(g24, subj_key)
        d23 = compute_dist(g23, subj_key)
        if d24 and d23:
            output['by_grade_yoy'][g][subj_name] = {
                'y23': d23, 'y24': d24,
                'delta': round(d24['proficient_pct'] - d23['proficient_pct'], 1)
            }

with open(os.path.join(BASE, 'leap_analysis.json'), 'w') as f:
    json.dump(output, f, indent=2)

print("\n\nSaved analysis to leap_analysis.json")
