import json, math
from collections import Counter, defaultdict

DATADIR = 'C:/Users/sshirey/bigquery-dashboards/research/assessment-alignment/run-05'

with open(f'{DATADIR}/composite_ela.json') as f:
    ela_data = json.load(f)
with open(f'{DATADIR}/composite_math.json') as f:
    math_data = json.load(f)

def assign_tier(anet_score):
    if anet_score is None: return None
    s = float(anet_score)
    if s < 20: return 'Crisis'
    if s < 30: return 'Intervention'
    if s < 50: return 'Watch'
    return 'On Track'

def is_proficient(level):
    return level in ('Mastery', 'Advanced')

def school_short(s):
    if not s: return '?'
    if 'Ashe' in s: return 'Ashe'
    if 'Green' in s: return 'Green'
    if 'Hughes' in s: return 'LHA'
    if 'Wheatley' in s: return 'Wheatley'
    return s[:10]

print("=== ELA RISK TIERS (based on anet BOY ELA) ===")
print(f"{'Tier':<16} {'N':>5} {'%U':>6} {'%AB':>6} {'%B':>6} {'%M':>6} {'%A':>6} {'Prof%':>7} {'MeanSS':>7}")
for tier in ['Crisis', 'Intervention', 'Watch', 'On Track']:
    students = [r for r in ela_data if assign_tier(r.get('anet_boy_ela')) == tier]
    n = len(students)
    if n == 0: continue
    levels = Counter(r['ela_level'] for r in students)
    prof = sum(1 for r in students if is_proficient(r['ela_level']))
    mean_ss = sum(float(r['ela_ss']) for r in students if r.get('ela_ss')) / n
    pcts = {lv: 100*levels.get(lv,0)/n for lv in ['Unsatisfactory','Approaching Basic','Basic','Mastery','Advanced']}
    print(f"{tier:<16} {n:>5} {pcts['Unsatisfactory']:>5.1f}% {pcts['Approaching Basic']:>5.1f}% {pcts['Basic']:>5.1f}% {pcts['Mastery']:>5.1f}% {pcts['Advanced']:>5.1f}% {100*prof/n:>6.1f}% {mean_ss:>7.0f}")

no_anet = sum(1 for r in ela_data if r.get('anet_boy_ela') is None)
print(f"  No anet BOY: {no_anet}")

print(f"\n=== MATH RISK TIERS (based on anet BOY Math) ===")
print(f"{'Tier':<16} {'N':>5} {'%U':>6} {'%AB':>6} {'%B':>6} {'%M':>6} {'%A':>6} {'Prof%':>7} {'MeanSS':>7}")
for tier in ['Crisis', 'Intervention', 'Watch', 'On Track']:
    students = [r for r in math_data if assign_tier(r.get('anet_boy_math')) == tier]
    n = len(students)
    if n == 0: continue
    levels = Counter(r['math_level'] for r in students)
    prof = sum(1 for r in students if is_proficient(r['math_level']))
    mean_ss = sum(float(r['math_ss']) for r in students if r.get('math_ss')) / n
    pcts = {lv: 100*levels.get(lv,0)/n for lv in ['Unsatisfactory','Approaching Basic','Basic','Mastery','Advanced']}
    print(f"{tier:<16} {n:>5} {pcts['Unsatisfactory']:>5.1f}% {pcts['Approaching Basic']:>5.1f}% {pcts['Basic']:>5.1f}% {pcts['Mastery']:>5.1f}% {pcts['Advanced']:>5.1f}% {100*prof/n:>6.1f}% {mean_ss:>7.0f}")

no_anet_m = sum(1 for r in math_data if r.get('anet_boy_math') is None)
print(f"  No anet BOY: {no_anet_m}")

# By school
print(f"\n=== ELA RISK TIERS BY SCHOOL ===")
for sch in ['Ashe', 'Green', 'LHA', 'Wheatley']:
    students = [r for r in ela_data if school_short(r.get('school','')) == sch and r.get('anet_boy_ela') is not None]
    tier_counts = Counter(assign_tier(r.get('anet_boy_ela')) for r in students)
    total = len(students)
    prof_by_tier = {}
    for tier in ['Crisis', 'Intervention', 'Watch', 'On Track']:
        t_students = [r for r in students if assign_tier(r.get('anet_boy_ela')) == tier]
        if t_students:
            prof_by_tier[tier] = 100 * sum(1 for r in t_students if is_proficient(r['ela_level'])) / len(t_students)
        else:
            prof_by_tier[tier] = 0
    print(f"  {sch}: Crisis {tier_counts.get('Crisis',0)} ({100*tier_counts.get('Crisis',0)/total:.0f}%), Intervention {tier_counts.get('Intervention',0)} ({100*tier_counts.get('Intervention',0)/total:.0f}%), Watch {tier_counts.get('Watch',0)} ({100*tier_counts.get('Watch',0)/total:.0f}%), On Track {tier_counts.get('On Track',0)} ({100*tier_counts.get('On Track',0)/total:.0f}%) | n={total}")
    print(f"    Prof rates: Crisis {prof_by_tier['Crisis']:.0f}%, Intervention {prof_by_tier['Intervention']:.0f}%, Watch {prof_by_tier['Watch']:.0f}%, On Track {prof_by_tier['On Track']:.0f}%")

print(f"\n=== MATH RISK TIERS BY SCHOOL ===")
for sch in ['Ashe', 'Green', 'LHA', 'Wheatley']:
    students = [r for r in math_data if school_short(r.get('school','')) == sch and r.get('anet_boy_math') is not None]
    tier_counts = Counter(assign_tier(r.get('anet_boy_math')) for r in students)
    total = len(students)
    if total == 0: continue
    prof_by_tier = {}
    for tier in ['Crisis', 'Intervention', 'Watch', 'On Track']:
        t_students = [r for r in students if assign_tier(r.get('anet_boy_math')) == tier]
        if t_students:
            prof_by_tier[tier] = 100 * sum(1 for r in t_students if is_proficient(r['math_level'])) / len(t_students)
        else:
            prof_by_tier[tier] = 0
    print(f"  {sch}: Crisis {tier_counts.get('Crisis',0)} ({100*tier_counts.get('Crisis',0)/total:.0f}%), Intervention {tier_counts.get('Intervention',0)} ({100*tier_counts.get('Intervention',0)/total:.0f}%), Watch {tier_counts.get('Watch',0)} ({100*tier_counts.get('Watch',0)/total:.0f}%), On Track {tier_counts.get('On Track',0)} ({100*tier_counts.get('On Track',0)/total:.0f}%) | n={total}")
    print(f"    Prof rates: Crisis {prof_by_tier['Crisis']:.0f}%, Intervention {prof_by_tier['Intervention']:.0f}%, Watch {prof_by_tier['Watch']:.0f}%, On Track {prof_by_tier['On Track']:.0f}%")

# By grade
print(f"\n=== ELA RISK TIERS BY GRADE ===")
for g in range(3, 9):
    students = [r for r in ela_data if r.get('grade') == g and r.get('anet_boy_ela') is not None]
    if not students: continue
    tier_counts = Counter(assign_tier(r.get('anet_boy_ela')) for r in students)
    total = len(students)
    prof_by_tier = {}
    for tier in ['Crisis', 'Intervention', 'Watch', 'On Track']:
        t_students = [r for r in students if assign_tier(r.get('anet_boy_ela')) == tier]
        if t_students:
            prof_by_tier[tier] = 100 * sum(1 for r in t_students if is_proficient(r['ela_level'])) / len(t_students)
        else:
            prof_by_tier[tier] = 0
    pcts = {t: 100*tier_counts.get(t,0)/total for t in ['Crisis','Intervention','Watch','On Track']}
    print(f"  G{g}: Crisis {pcts['Crisis']:.0f}% ({tier_counts.get('Crisis',0)}), Interv {pcts['Intervention']:.0f}% ({tier_counts.get('Intervention',0)}), Watch {pcts['Watch']:.0f}% ({tier_counts.get('Watch',0)}), OnTrack {pcts['On Track']:.0f}% ({tier_counts.get('On Track',0)}) | n={total}")

print(f"\n=== MATH RISK TIERS BY GRADE ===")
for g in range(3, 9):
    students = [r for r in math_data if r.get('grade') == g and r.get('anet_boy_math') is not None]
    if not students: continue
    tier_counts = Counter(assign_tier(r.get('anet_boy_math')) for r in students)
    total = len(students)
    pcts = {t: 100*tier_counts.get(t,0)/total for t in ['Crisis','Intervention','Watch','On Track']}
    print(f"  G{g}: Crisis {pcts['Crisis']:.0f}% ({tier_counts.get('Crisis',0)}), Interv {pcts['Intervention']:.0f}% ({tier_counts.get('Intervention',0)}), Watch {pcts['Watch']:.0f}% ({tier_counts.get('Watch',0)}), OnTrack {pcts['On Track']:.0f}% ({tier_counts.get('On Track',0)}) | n={total}")

# Effect sizes
print(f"\n=== EFFECT SIZES (Cohen's d between tiers) ===")
def cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    if n1 < 5 or n2 < 5: return None
    m1, m2 = sum(group1)/n1, sum(group2)/n2
    s1 = math.sqrt(sum((x-m1)**2 for x in group1) / (n1-1))
    s2 = math.sqrt(sum((x-m2)**2 for x in group2) / (n2-1))
    sp = math.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1+n2-2))
    if sp == 0: return None
    return (m2 - m1) / sp

# Crisis vs On Track
crisis_ela = [float(r['ela_ss']) for r in ela_data if assign_tier(r.get('anet_boy_ela')) == 'Crisis' and r.get('ela_ss')]
ontrack_ela = [float(r['ela_ss']) for r in ela_data if assign_tier(r.get('anet_boy_ela')) == 'On Track' and r.get('ela_ss')]
d = cohens_d(crisis_ela, ontrack_ela)
print(f"  ELA: Crisis vs On Track: d={d:.2f} (n1={len(crisis_ela)}, n2={len(ontrack_ela)})")

crisis_math = [float(r['math_ss']) for r in math_data if assign_tier(r.get('anet_boy_math')) == 'Crisis' and r.get('math_ss')]
ontrack_math = [float(r['math_ss']) for r in math_data if assign_tier(r.get('anet_boy_math')) == 'On Track' and r.get('math_ss')]
d_m = cohens_d(crisis_math, ontrack_math)
print(f"  Math: Crisis vs On Track: d={d_m:.2f} (n1={len(crisis_math)}, n2={len(ontrack_math)})")

# Intervention vs Watch
interv_ela = [float(r['ela_ss']) for r in ela_data if assign_tier(r.get('anet_boy_ela')) == 'Intervention' and r.get('ela_ss')]
watch_ela = [float(r['ela_ss']) for r in ela_data if assign_tier(r.get('anet_boy_ela')) == 'Watch' and r.get('ela_ss')]
d2 = cohens_d(interv_ela, watch_ela)
print(f"  ELA: Intervention vs Watch: d={d2:.2f}")

interv_math = [float(r['math_ss']) for r in math_data if assign_tier(r.get('anet_boy_math')) == 'Intervention' and r.get('math_ss')]
watch_math = [float(r['math_ss']) for r in math_data if assign_tier(r.get('anet_boy_math')) == 'Watch' and r.get('math_ss')]
d2m = cohens_d(interv_math, watch_math)
print(f"  Math: Intervention vs Watch: d={d2m:.2f}")
