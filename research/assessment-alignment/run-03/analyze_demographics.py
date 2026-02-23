import json, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))

# Load demographics from _full tables (Green, Ashe, Wheatley - no LHA _full)
with open(os.path.join(BASE, 'leap_24_25_demo.json')) as f:
    demo_data = json.load(f)

# Load bottom 25th
with open(os.path.join(BASE, 'bottom25_with_roster.json')) as f:
    bottom25 = json.load(f)

# Load bottom 25 raw (has flags but no school/grade)
with open(os.path.join(BASE, 'bottom25_full.json')) as f:
    bottom25_raw = json.load(f)

# Load LEAP Connect
with open(os.path.join(BASE, 'leap_connect_24_25.json')) as f:
    lc_2425 = json.load(f)
with open(os.path.join(BASE, 'leap_connect_23_24.json')) as f:
    lc_2324 = json.load(f)

def short_school(s):
    if not s: return 'Unknown'
    if 'Ashe' in s: return 'Ashe'
    if 'Green' in s: return 'Green'
    if 'Hughes' in s: return 'LHA'
    if 'Wheatley' in s: return 'Wheatley'
    return s

# ============================================================
# Demographics from _full tables
# ============================================================
print("=" * 80)
print("LEAP 24-25 DEMOGRAPHICS (from _full tables, 3 schools)")
print("=" * 80)
print(f"Total records: {len(demo_data)}")

# Schools represented
schools_in_demo = defaultdict(int)
for r in demo_data:
    schools_in_demo[short_school(r.get('school',''))] += 1
print(f"\nSchools: {dict(schools_in_demo)}")

# Ethnicity breakdown
eth_counts = defaultdict(int)
for r in demo_data:
    eth_counts[r.get('ethnicity','Unknown')] += 1
print("\nEthnicity:")
for e, c in sorted(eth_counts.items(), key=lambda x: -x[1]):
    print(f"  {e}: {c} ({100*c/len(demo_data):.1f}%)")

# Gender
gender_counts = defaultdict(int)
for r in demo_data:
    gender_counts[r.get('Gender','Unknown')] += 1
print(f"\nGender: {dict(gender_counts)}")

# SPED
sped_counts = defaultdict(int)
for r in demo_data:
    sped_counts[r.get('sped_status','Unknown')] += 1
print(f"\nSPED Status:")
for s, c in sorted(sped_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c} ({100*c/len(demo_data):.1f}%)")

# EL Status
el_counts = defaultdict(int)
for r in demo_data:
    el_counts[r.get('el_status','Unknown')] += 1
print(f"\nEL Status: {dict(el_counts)}")

# Econ disadvantaged
econ_counts = defaultdict(int)
for r in demo_data:
    econ_counts[r.get('econ_status','Unknown')] += 1
print(f"\nEconomic Status: {dict(econ_counts)}")

# Proficiency by SPED status
ordered_levels = ['Unsatisfactory', 'Approaching Basic', 'Basic', 'Mastery', 'Advanced']
print("\n--- Proficiency by SPED Status ---")
for sped in ['Regular', 'Special Education']:
    subset = [r for r in demo_data if r.get('sped_status','') == sped]
    for subj, key in [('ELA', 'ela_level'), ('Math', 'math_level')]:
        valid = [r for r in subset if (r.get(key) or '').strip() in ordered_levels]
        if valid:
            prof = sum(1 for r in valid if r[key] in ['Mastery','Advanced'])
            print(f"  {sped} {subj}: {100*prof/len(valid):.1f}% proficient (n={len(valid)})")

# Proficiency by ethnicity
print("\n--- Proficiency by Ethnicity ---")
for eth in ['Black or African American', 'Hispanic or Latino', 'White', 'Two or more races']:
    subset = [r for r in demo_data if r.get('ethnicity','') == eth]
    if len(subset) < 10: continue
    for subj, key in [('ELA', 'ela_level'), ('Math', 'math_level')]:
        valid = [r for r in subset if (r.get(key) or '').strip() in ordered_levels]
        if valid:
            prof = sum(1 for r in valid if r[key] in ['Mastery','Advanced'])
            print(f"  {eth} {subj}: {100*prof/len(valid):.1f}% proficient (n={len(valid)})")

# Remediation needed
remed_counts = defaultdict(int)
for r in demo_data:
    remed_counts[r.get('RemediationNeeded','Unknown')] += 1
print(f"\nRemediation Needed: {dict(remed_counts)}")

# ============================================================
# Bottom 25th Percentile Analysis
# ============================================================
print("\n" + "=" * 80)
print("BOTTOM 25TH PERCENTILE ANALYSIS")
print("=" * 80)
print(f"Total records in table: {len(bottom25_raw)}")

# Count by flag type
ela_25 = sum(1 for r in bottom25_raw if r.get('ELA_25th') == 'Yes')
math_25 = sum(1 for r in bottom25_raw if r.get('Math_25th') == 'Yes')
dibels_25 = sum(1 for r in bottom25_raw if r.get('DIBELS_25th') == 'Yes')
dibels_ela_25 = sum(1 for r in bottom25_raw if r.get('DIBELS_ELA_25th') == 'Yes')
bottom_any = sum(1 for r in bottom25_raw if r.get('Bottom_25th') == 'Yes')

print(f"\nStudents flagged:")
print(f"  Bottom 25th (any): {bottom_any}")
print(f"  ELA Bottom 25th: {ela_25}")
print(f"  Math Bottom 25th: {math_25}")
print(f"  DIBELS Bottom 25th: {dibels_25}")
print(f"  DIBELS ELA Bottom 25th: {dibels_ela_25}")

# Bottom 25 by school
print(f"\nBottom 25th (any=Yes) by School (from roster join, n={len(bottom25)}):")
b25_by_school = defaultdict(lambda: {'total': 0, 'flagged': 0, 'ela': 0, 'math': 0})
for r in bottom25:
    sch = short_school(r.get('school',''))
    b25_by_school[sch]['total'] += 1
    if r.get('Bottom_25th') == 'Yes':
        b25_by_school[sch]['flagged'] += 1
    if r.get('ELA_25th') == 'Yes':
        b25_by_school[sch]['ela'] += 1
    if r.get('Math_25th') == 'Yes':
        b25_by_school[sch]['math'] += 1

for sch in ['Ashe', 'Green', 'LHA', 'Wheatley', 'Unknown']:
    d = b25_by_school.get(sch, {'total':0, 'flagged':0, 'ela':0, 'math':0})
    if d['total'] > 0:
        print(f"  {sch}: {d['flagged']} flagged / {d['total']} total ({100*d['flagged']/d['total']:.1f}%), ELA={d['ela']}, Math={d['math']}")

# Bottom 25 by grade
print(f"\nBottom 25th (any=Yes) by Grade:")
b25_by_grade = defaultdict(lambda: {'total': 0, 'flagged': 0})
for r in bottom25:
    g = str(r.get('grade', 'Unknown'))
    b25_by_grade[g]['total'] += 1
    if r.get('Bottom_25th') == 'Yes':
        b25_by_grade[g]['flagged'] += 1

for g in sorted(b25_by_grade.keys(), key=lambda x: int(x) if x.isdigit() else 99):
    d = b25_by_grade[g]
    if d['total'] > 0:
        print(f"  Grade {g}: {d['flagged']} flagged / {d['total']} total ({100*d['flagged']/d['total']:.1f}%)")

# ============================================================
# LEAP Connect Analysis
# ============================================================
print("\n" + "=" * 80)
print("LEAP CONNECT (ALTERNATE ASSESSMENT)")
print("=" * 80)

print(f"\n24-25: {len(lc_2425)} students")
print(f"23-24: {len(lc_2324)} students")

# By school
print("\n24-25 by School:")
lc_by_school = defaultdict(int)
for r in lc_2425:
    lc_by_school[short_school(r.get('school',''))] += 1
for sch in sorted(lc_by_school.keys()):
    print(f"  {sch}: {lc_by_school[sch]}")

# By grade
print("\n24-25 by Grade:")
lc_by_grade = defaultdict(int)
for r in lc_2425:
    lc_by_grade[r.get('Grade','')] += 1
for g in sorted(lc_by_grade.keys()):
    print(f"  Grade {g}: {lc_by_grade[g]}")

# SPED categories
print("\n24-25 SPED Categories:")
lc_sped = defaultdict(int)
for r in lc_2425:
    lc_sped[r.get('sped_cat','')] += 1
for s, c in sorted(lc_sped.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

# Achievement levels
print("\n24-25 ELA Achievement:")
lc_ela = defaultdict(int)
for r in lc_2425:
    lc_ela[r.get('ela_level','')] += 1
for l, c in sorted(lc_ela.items(), key=lambda x: -x[1]):
    print(f"  {l}: {c}")

print("\n24-25 Math Achievement:")
lc_math = defaultdict(int)
for r in lc_2425:
    lc_math[r.get('math_level','')] += 1
for l, c in sorted(lc_math.items(), key=lambda x: -x[1]):
    print(f"  {l}: {c}")

# Demographics
print("\n24-25 Demographics:")
lc_eth = defaultdict(int)
for r in lc_2425:
    lc_eth[r.get('ethnicity','')] += 1
for e, c in sorted(lc_eth.items(), key=lambda x: -x[1]):
    print(f"  {e}: {c}")

lc_gen = defaultdict(int)
for r in lc_2425:
    lc_gen[r.get('gender','')] += 1
print(f"  Gender: {dict(lc_gen)}")

# YoY comparison
print("\n23-24 by School:")
lc_by_school_23 = defaultdict(int)
for r in lc_2324:
    lc_by_school_23[short_school(r.get('school',''))] += 1
for sch in sorted(lc_by_school_23.keys()):
    print(f"  {sch}: {lc_by_school_23[sch]}")
