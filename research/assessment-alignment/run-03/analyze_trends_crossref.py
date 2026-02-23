import json, os, statistics
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'leap_22_23_raw.json')) as f:
    data_2223 = json.load(f)
with open(os.path.join(BASE, 'leap_23_24_raw.json')) as f:
    data_2324 = json.load(f)
with open(os.path.join(BASE, 'leap_24_25_raw.json')) as f:
    data_2425 = json.load(f)
with open(os.path.join(BASE, 'leap_internal_crossref.json')) as f:
    crossref = json.load(f)

# Convert numeric fields from string to float
numeric_fields = ['leap_ela_ss', 'leap_math_ss', 'anet_boy_ela_pct', 'anet_boy_math_pct',
                  'anet_eoy_ela_pct', 'anet_eoy_math_pct', 'map_boy_ela_rit', 'map_boy_ela_pct',
                  'map_boy_math_rit', 'map_boy_math_pct']
for r in crossref:
    for f in numeric_fields:
        if r.get(f) is not None:
            try:
                r[f] = float(r[f])
            except (ValueError, TypeError):
                r[f] = None

# Normalize
for r in data_2223:
    r['Grade'] = str(int(r['Grade'])) if r.get('Grade','').strip() else r['Grade']
for r in data_2324:
    r['Grade'] = str(int(r['Grade'])) if r.get('Grade','').strip() else r['Grade']
for r in data_2425:
    r['Grade'] = str(int(r['Grade'])) if r.get('Grade','').strip() else r['Grade']

def short_school(s):
    if not s: return 'Unknown'
    if 'Ashe' in s: return 'Ashe'
    if 'Green' in s: return 'Green'
    if 'Hughes' in s: return 'LHA'
    if 'Wheatley' in s: return 'Wheatley'
    return s

ordered_levels = ['Unsatisfactory', 'Approaching Basic', 'Basic', 'Mastery', 'Advanced']

def compute_prof(records, key):
    valid = [r for r in records if (r.get(key) or '').strip() in ordered_levels]
    if not valid: return None, 0
    prof = sum(1 for r in valid if r[key] in ['Mastery','Advanced'])
    return round(100 * prof / len(valid), 1), len(valid)

# ============================================================
# 3-YEAR TREND: 22-23 -> 23-24 -> 24-25
# ============================================================
print("=" * 80)
print("3-YEAR NETWORK TREND (22-23 -> 23-24 -> 24-25)")
print("=" * 80)
print(f"22-23: n={len(data_2223)}, 23-24: n={len(data_2324)}, 24-25: n={len(data_2425)}")

for subj_key, subj_name in [('ela_level','ELA'), ('math_level','Math'), ('sci_level','Science')]:
    p22, n22 = compute_prof(data_2223, subj_key)
    p23, n23 = compute_prof(data_2324, subj_key)
    p24, n24 = compute_prof(data_2425, subj_key)
    if p22 is not None and p23 is not None and p24 is not None:
        print(f"  {subj_name}: {p22}% (n={n22}) -> {p23}% (n={n23}) -> {p24}% (n={n24})  [{p24-p22:+.1f}pp 2yr]")

# By school 3-year trend
print("\n" + "=" * 80)
print("3-YEAR SCHOOL TRENDS")
print("=" * 80)
for sch in ['Ashe','Green','LHA','Wheatley']:
    s22 = [r for r in data_2223 if short_school(r.get('school',''))==sch]
    s23 = [r for r in data_2324 if short_school(r.get('school',''))==sch]
    s24 = [r for r in data_2425 if short_school(r.get('school',''))==sch]
    print(f"\n{sch} (n: {len(s22)}->{len(s23)}->{len(s24)}):")
    for subj_key, subj_name in [('ela_level','ELA'), ('math_level','Math')]:
        p22, n22 = compute_prof(s22, subj_key)
        p23, n23 = compute_prof(s23, subj_key)
        p24, n24 = compute_prof(s24, subj_key)
        if p22 is not None:
            print(f"  {subj_name}: {p22}% -> {p23}% -> {p24}%  [{p24-p22:+.1f}pp 2yr]")

# ============================================================
# CROSS-REFERENCE ANALYSIS
# ============================================================
print("\n" + "=" * 80)
print("LEAP x INTERNAL ASSESSMENT CROSS-REFERENCE")
print("=" * 80)
print(f"Total LEAP records: {len(crossref)}")

# Coverage
has_anet_boy_ela = sum(1 for r in crossref if r.get('anet_boy_ela_pct') is not None)
has_anet_boy_math = sum(1 for r in crossref if r.get('anet_boy_math_pct') is not None)
has_anet_eoy_ela = sum(1 for r in crossref if r.get('anet_eoy_ela_pct') is not None)
has_anet_eoy_math = sum(1 for r in crossref if r.get('anet_eoy_math_pct') is not None)
has_map_ela = sum(1 for r in crossref if r.get('map_boy_ela_rit') is not None)
has_map_math = sum(1 for r in crossref if r.get('map_boy_math_rit') is not None)

print(f"\nCoverage (of {len(crossref)} LEAP students):")
print(f"  anet BOY ELA: {has_anet_boy_ela} ({100*has_anet_boy_ela/len(crossref):.1f}%)")
print(f"  anet BOY Math: {has_anet_boy_math} ({100*has_anet_boy_math/len(crossref):.1f}%)")
print(f"  anet EOY ELA: {has_anet_eoy_ela} ({100*has_anet_eoy_ela/len(crossref):.1f}%)")
print(f"  anet EOY Math: {has_anet_eoy_math} ({100*has_anet_eoy_math/len(crossref):.1f}%)")
print(f"  MAP BOY ELA: {has_map_ela} ({100*has_map_ela/len(crossref):.1f}%)")
print(f"  MAP BOY Math: {has_map_math} ({100*has_map_math/len(crossref):.1f}%)")

# Mean internal scores by LEAP achievement level
print("\n--- Mean anet BOY % by LEAP Achievement Level ---")
for subj_key, anet_key, subj_name in [('ela_level','anet_boy_ela_pct','ELA'), ('math_level','anet_boy_math_pct','Math')]:
    print(f"\n  {subj_name}:")
    for lev in ordered_levels:
        subset = [r for r in crossref if r.get(subj_key)==lev and r.get(anet_key) is not None]
        if subset:
            scores = [r[anet_key] for r in subset]
            print(f"    {lev:20s}: mean={statistics.mean(scores):.1f}%, sd={statistics.stdev(scores):.1f}%, n={len(subset)}")

print("\n--- Mean MAP BOY RIT by LEAP Achievement Level ---")
for subj_key, map_key, subj_name in [('ela_level','map_boy_ela_rit','ELA'), ('math_level','map_boy_math_rit','Math')]:
    print(f"\n  {subj_name}:")
    for lev in ordered_levels:
        subset = [r for r in crossref if r.get(subj_key)==lev and r.get(map_key) is not None]
        if subset:
            scores = [r[map_key] for r in subset]
            print(f"    {lev:20s}: mean={statistics.mean(scores):.1f}, sd={statistics.stdev(scores):.1f}, n={len(subset)}")

print("\n--- Mean MAP BOY Percentile by LEAP Achievement Level ---")
for subj_key, map_key, subj_name in [('ela_level','map_boy_ela_pct','ELA'), ('math_level','map_boy_math_pct','Math')]:
    print(f"\n  {subj_name}:")
    for lev in ordered_levels:
        subset = [r for r in crossref if r.get(subj_key)==lev and r.get(map_key) is not None]
        if subset:
            scores = [r[map_key] for r in subset]
            print(f"    {lev:20s}: mean={statistics.mean(scores):.1f}, sd={statistics.stdev(scores):.1f}, n={len(subset)}")

# Correlation: anet BOY -> LEAP scale score
print("\n--- Pearson Correlations ---")
def pearson(x, y):
    n = len(x)
    if n < 3: return None
    mx, my = sum(x)/n, sum(y)/n
    cov = sum((xi-mx)*(yi-my) for xi,yi in zip(x,y)) / (n-1)
    sx = (sum((xi-mx)**2 for xi in x) / (n-1)) ** 0.5
    sy = (sum((yi-my)**2 for yi in y) / (n-1)) ** 0.5
    if sx == 0 or sy == 0: return None
    return cov / (sx * sy)

pairs = [
    ('anet_boy_ela_pct', 'leap_ela_ss', 'anet BOY ELA % -> LEAP ELA SS'),
    ('anet_boy_math_pct', 'leap_math_ss', 'anet BOY Math % -> LEAP Math SS'),
    ('anet_eoy_ela_pct', 'leap_ela_ss', 'anet EOY ELA % -> LEAP ELA SS'),
    ('anet_eoy_math_pct', 'leap_math_ss', 'anet EOY Math % -> LEAP Math SS'),
    ('map_boy_ela_rit', 'leap_ela_ss', 'MAP BOY ELA RIT -> LEAP ELA SS'),
    ('map_boy_math_rit', 'leap_math_ss', 'MAP BOY Math RIT -> LEAP Math SS'),
    ('map_boy_ela_pct', 'leap_ela_ss', 'MAP BOY ELA %ile -> LEAP ELA SS'),
    ('map_boy_math_pct', 'leap_math_ss', 'MAP BOY Math %ile -> LEAP Math SS'),
]

for x_key, y_key, label in pairs:
    valid = [(r[x_key], r[y_key]) for r in crossref if r.get(x_key) is not None and r.get(y_key) is not None]
    if valid:
        x_vals = [v[0] for v in valid]
        y_vals = [v[1] for v in valid]
        r = pearson(x_vals, y_vals)
        if r is not None:
            print(f"  {label}: r={r:.3f} (n={len(valid)})")

# Threshold analysis: anet BOY cutoff for identifying Unsatisfactory on LEAP
print("\n--- anet BOY Threshold Analysis for LEAP Unsatisfactory ---")
for subj_key, anet_key, subj_name in [('ela_level','anet_boy_ela_pct','ELA'), ('math_level','anet_boy_math_pct','Math')]:
    valid = [r for r in crossref if r.get(anet_key) is not None and (r.get(subj_key) or '').strip() in ordered_levels]
    for threshold in [25, 30, 35, 40]:
        below = [r for r in valid if r[anet_key] < threshold]
        above = [r for r in valid if r[anet_key] >= threshold]
        if below and above:
            unsat_below = sum(1 for r in below if r[subj_key] == 'Unsatisfactory')
            unsat_above = sum(1 for r in above if r[subj_key] == 'Unsatisfactory')
            total_unsat = sum(1 for r in valid if r[subj_key] == 'Unsatisfactory')
            sensitivity = 100 * unsat_below / total_unsat if total_unsat > 0 else 0
            ppv = 100 * unsat_below / len(below) if len(below) > 0 else 0
            print(f"  {subj_name} <{threshold}%: sensitivity={sensitivity:.1f}% (catches {unsat_below}/{total_unsat} Unsat), PPV={ppv:.1f}% ({unsat_below}/{len(below)} below threshold are Unsat)")

# Save 3-year trend data for HTML
trend_data = {'network': {}, 'by_school': {}}
for year, data, label in [(data_2223, data_2223, '22_23'), (data_2324, data_2324, '23_24'), (data_2425, data_2425, '24_25')]:
    trend_data['network'][label] = {}
    for subj_key, subj_name in [('ela_level','ELA'), ('math_level','Math'), ('sci_level','Science')]:
        p, n = compute_prof(data, subj_key)
        if p is not None:
            trend_data['network'][label][subj_name] = {'proficient_pct': p, 'n': n}
    for sch in ['Ashe','Green','LHA','Wheatley']:
        if sch not in trend_data['by_school']:
            trend_data['by_school'][sch] = {}
        sch_data = [r for r in data if short_school(r.get('school',''))==sch]
        trend_data['by_school'][sch][label] = {}
        for subj_key, subj_name in [('ela_level','ELA'), ('math_level','Math')]:
            p, n = compute_prof(sch_data, subj_key)
            if p is not None:
                trend_data['by_school'][sch][label][subj_name] = {'proficient_pct': p, 'n': n}

with open(os.path.join(BASE, 'trend_data.json'), 'w') as f:
    json.dump(trend_data, f, indent=2)

print("\n\nSaved trend_data.json")
