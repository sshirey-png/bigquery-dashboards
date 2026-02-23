import json, math
from collections import Counter

DATADIR = 'C:/Users/sshirey/bigquery-dashboards/research/assessment-alignment/run-05'

with open(f'{DATADIR}/sped_el.json') as f:
    data = json.load(f)

print(f"Total students: {len(data)}")

# Check grade field type
grades = [r.get('grade') for r in data[:20]]
print(f"Sample grades: {grades}")
print(f"Grade types: {[type(g).__name__ for g in grades]}")

# SPED status values
sped_vals = Counter(r.get('sped_status','MISSING') for r in data)
print(f"\nSPED status values: {dict(sped_vals)}")

ell_vals = Counter(r.get('ell_status','MISSING') for r in data)
print(f"ELL status values: {dict(ell_vals)}")

frl_vals = Counter(r.get('frl_status','MISSING') for r in data)
print(f"FRL status values: {dict(frl_vals)}")

gender_vals = Counter(r.get('gender','MISSING') for r in data)
print(f"Gender values: {dict(gender_vals)}")

race_vals = Counter(r.get('race','MISSING') for r in data)
print(f"Race values: {dict(race_vals)}")

# SPED concordance
def is_sped(r):
    return r.get('sped_status','') in ('Y', 'Yes', 'TRUE', 'true', '1', 'IEP')

def is_ell(r):
    return r.get('ell_status','') in ('Y', 'Yes', 'TRUE', 'true', '1', 'ELL', 'EL')

# Check more carefully what the actual values are
print(f"\n=== SPED Analysis ===")
sped_students = [r for r in data if is_sped(r)]
non_sped = [r for r in data if not is_sped(r) and r.get('sped_status') is not None and r.get('sped_status') != 'MISSING']
print(f"SPED students: {len(sped_students)}")
print(f"Non-SPED: {len(non_sped)}")

# If SPED values are unusual, let's check
if len(sped_students) == 0:
    print("No SPED students found with expected values. Checking actual values...")
    for val, count in sped_vals.items():
        if val not in (None, 'MISSING', '', 'N', 'No', 'FALSE', 'false', '0'):
            print(f"  Potential SPED value: '{val}' (n={count})")

# ELL analysis
ell_students = [r for r in data if is_ell(r)]
non_ell = [r for r in data if not is_ell(r) and r.get('ell_status') is not None and r.get('ell_status') != 'MISSING']
print(f"\n=== ELL Analysis ===")
print(f"ELL students: {len(ell_students)}")
print(f"Non-ELL: {len(non_ell)}")

if len(ell_students) == 0:
    print("No ELL students found. Checking actual values...")
    for val, count in ell_vals.items():
        if val not in (None, 'MISSING', '', 'N', 'No', 'FALSE', 'false', '0'):
            print(f"  Potential ELL value: '{val}' (n={count})")

# FRL analysis
print(f"\n=== FRL Analysis ===")
frl_students = [r for r in data if r.get('frl_status','') in ('Y', 'Yes', 'TRUE', 'true', '1', 'FRL', 'Free', 'Reduced')]
print(f"FRL students: {len(frl_students)}")

# Concordance by demographics - use whatever groups we found
# First just do gender analysis since we know those values
print(f"\n=== CONCORDANCE BY GENDER ===")
for gen in ['Female', 'Male', 'F', 'M']:
    gen_students = [r for r in data if r.get('gender') == gen]
    if not gen_students: continue
    n = len(gen_students)
    ela_prof = sum(1 for r in gen_students if r.get('leap_ela_prof') == 1)
    math_prof = sum(1 for r in gen_students if r.get('leap_math_prof') == 1)
    ela_inflated = sum(1 for r in gen_students if r.get('ela_inflated') == 1)
    math_inflated = sum(1 for r in gen_students if r.get('math_inflated') == 1)
    anet_ela_risk = sum(1 for r in gen_students if r.get('anet_ela_atrisk') == 1)
    anet_math_risk = sum(1 for r in gen_students if r.get('anet_math_atrisk') == 1)
    print(f"  {gen}: n={n}, ELA prof {100*ela_prof/n:.1f}%, Math prof {100*math_prof/n:.1f}%, ELA inflated {100*ela_inflated/n:.1f}%, Math inflated {100*math_inflated/n:.1f}%, ELA at-risk {100*anet_ela_risk/n:.1f}%, Math at-risk {100*anet_math_risk/n:.1f}%")

print(f"\n=== CONCORDANCE BY RACE ===")
for race_val, count in sorted(race_vals.items(), key=lambda x: -x[1]):
    if race_val in (None, 'MISSING', '') or count < 20: continue
    race_students = [r for r in data if r.get('race') == race_val]
    n = len(race_students)
    ela_prof = sum(1 for r in race_students if r.get('leap_ela_prof') == 1)
    math_prof = sum(1 for r in race_students if r.get('leap_math_prof') == 1)
    ela_inflated = sum(1 for r in race_students if r.get('ela_inflated') == 1)
    math_inflated = sum(1 for r in race_students if r.get('math_inflated') == 1)
    print(f"  {race_val}: n={n}, ELA prof {100*ela_prof/n:.1f}%, Math prof {100*math_prof/n:.1f}%, ELA inflated {100*ela_inflated/n:.1f}%, Math inflated {100*math_inflated/n:.1f}%")

# Grade-level analysis
print(f"\n=== GRADE-LEVEL ANALYSIS ===")
grade_vals = Counter(r.get('grade') for r in data)
for g, cnt in sorted(grade_vals.items(), key=lambda x: (x[0] if x[0] is not None else -1)):
    print(f"  Grade {g}: {cnt}")

# Inflate rates by grade
print(f"\n=== INFLATION RATES BY GRADE ===")
for g in sorted(set(r.get('grade') for r in data if r.get('grade') is not None)):
    grade_students = [r for r in data if r.get('grade') == g]
    n = len(grade_students)
    if n < 10: continue
    ela_inflated = sum(1 for r in grade_students if r.get('ela_inflated') == 1)
    math_inflated = sum(1 for r in grade_students if r.get('math_inflated') == 1)
    ela_n = sum(1 for r in grade_students if r.get('grade_ela') is not None)
    math_n = sum(1 for r in grade_students if r.get('grade_math') is not None)
    print(f"  Grade {g}: ELA inflated {ela_inflated}/{ela_n} ({100*ela_inflated/max(ela_n,1):.1f}%), Math inflated {math_inflated}/{math_n} ({100*math_inflated/max(math_n,1):.1f}%)")
