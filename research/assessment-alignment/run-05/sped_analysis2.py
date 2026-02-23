import json, math
from collections import Counter

DATADIR = 'C:/Users/sshirey/bigquery-dashboards/research/assessment-alignment/run-05'

with open(f'{DATADIR}/sped_full.json') as f:
    data = json.load(f)

print(f"Total students (3 schools with _full data): {len(data)}")

# Check demographics
sped_vals = Counter(r.get('sped_class') for r in data)
print(f"SPED classification: {dict(sped_vals)}")

lep_vals = Counter(r.get('lep') for r in data)
print(f"LEP status: {dict(lep_vals)}")

econ_vals = Counter(r.get('econ_disadv') for r in data)
print(f"Economically disadvantaged: {dict(econ_vals)}")

def assign_tier(score):
    if score is None: return None
    s = float(score)
    if s < 20: return 'Crisis'
    if s < 30: return 'Intervention'
    if s < 50: return 'Watch'
    return 'On Track'

def is_prof(level):
    return level in ('Mastery', 'Advanced')

def school_short(s):
    if not s: return '?'
    if 'Ashe' in s: return 'Ashe'
    if 'Green' in s: return 'Green'
    if 'Hughes' in s: return 'LHA'
    if 'Wheatley' in s: return 'Wheatley'
    return s[:10]

# SPED concordance
print("\n=== SPED vs Non-SPED: Risk Tiers and Outcomes ===")
for sped_label, sped_filter in [('SPED', lambda r: r.get('sped_class') == 'Special'),
                                  ('Regular', lambda r: r.get('sped_class') == 'Regular')]:
    students = [r for r in data if sped_filter(r)]
    n = len(students)
    if n == 0: continue

    ela_prof = sum(1 for r in students if is_prof(r.get('ela_level','')))
    math_prof = sum(1 for r in students if is_prof(r.get('math_level','')))

    # Grade inflation
    ela_inflated = sum(1 for r in students
                       if r.get('grade_ela') is not None and float(r['grade_ela']) >= 80
                       and r.get('ela_level') in ('Unsatisfactory', 'Approaching Basic'))
    math_inflated = sum(1 for r in students
                        if r.get('grade_math') is not None and float(r['grade_math']) >= 80
                        and r.get('math_level') in ('Unsatisfactory', 'Approaching Basic'))
    has_grade_ela = sum(1 for r in students if r.get('grade_ela') is not None)
    has_grade_math = sum(1 for r in students if r.get('grade_math') is not None)

    # Risk tiers
    tier_ela = Counter(assign_tier(r.get('anet_boy_ela')) for r in students if r.get('anet_boy_ela') is not None)
    tier_math = Counter(assign_tier(r.get('anet_boy_math')) for r in students if r.get('anet_boy_math') is not None)
    tier_ela_total = sum(tier_ela.values())
    tier_math_total = sum(tier_math.values())

    # Mean anet scores
    anet_ela = [float(r['anet_boy_ela']) for r in students if r.get('anet_boy_ela') is not None]
    anet_math = [float(r['anet_boy_math']) for r in students if r.get('anet_boy_math') is not None]
    mean_anet_ela = sum(anet_ela)/len(anet_ela) if anet_ela else 0
    mean_anet_math = sum(anet_math)/len(anet_math) if anet_math else 0

    # Mean course grades
    grades_ela = [float(r['grade_ela']) for r in students if r.get('grade_ela') is not None]
    grades_math = [float(r['grade_math']) for r in students if r.get('grade_math') is not None]
    mean_grade_ela = sum(grades_ela)/len(grades_ela) if grades_ela else 0
    mean_grade_math = sum(grades_math)/len(grades_math) if grades_math else 0

    print(f"\n  {sped_label} (n={n}):")
    print(f"    LEAP prof: ELA {100*ela_prof/n:.1f}%, Math {100*math_prof/n:.1f}%")
    print(f"    Mean anet BOY: ELA {mean_anet_ela:.1f}%, Math {mean_anet_math:.1f}%")
    print(f"    Mean course grade: ELA {mean_grade_ela:.1f}%, Math {mean_grade_math:.1f}%")
    print(f"    Grade inflation: ELA {ela_inflated}/{has_grade_ela} ({100*ela_inflated/max(has_grade_ela,1):.1f}%), Math {math_inflated}/{has_grade_math} ({100*math_inflated/max(has_grade_math,1):.1f}%)")
    if tier_ela_total > 0:
        print(f"    ELA risk tiers: Crisis {tier_ela.get('Crisis',0)} ({100*tier_ela.get('Crisis',0)/tier_ela_total:.0f}%), Interv {tier_ela.get('Intervention',0)} ({100*tier_ela.get('Intervention',0)/tier_ela_total:.0f}%), Watch {tier_ela.get('Watch',0)} ({100*tier_ela.get('Watch',0)/tier_ela_total:.0f}%), OnTrack {tier_ela.get('On Track',0)} ({100*tier_ela.get('On Track',0)/tier_ela_total:.0f}%)")
    if tier_math_total > 0:
        print(f"    Math risk tiers: Crisis {tier_math.get('Crisis',0)} ({100*tier_math.get('Crisis',0)/tier_math_total:.0f}%), Interv {tier_math.get('Intervention',0)} ({100*tier_math.get('Intervention',0)/tier_math_total:.0f}%), Watch {tier_math.get('Watch',0)} ({100*tier_math.get('Watch',0)/tier_math_total:.0f}%), OnTrack {tier_math.get('On Track',0)} ({100*tier_math.get('On Track',0)/tier_math_total:.0f}%)")

# EL concordance
print("\n=== EL vs Non-EL: Risk Tiers and Outcomes ===")
for el_label, el_filter in [('EL', lambda r: r.get('lep') == 'Yes'),
                              ('Not EL', lambda r: r.get('lep') != 'Yes')]:
    students = [r for r in data if el_filter(r)]
    n = len(students)
    if n == 0: continue

    ela_prof = sum(1 for r in students if is_prof(r.get('ela_level','')))
    math_prof = sum(1 for r in students if is_prof(r.get('math_level','')))

    ela_inflated = sum(1 for r in students
                       if r.get('grade_ela') is not None and float(r['grade_ela']) >= 80
                       and r.get('ela_level') in ('Unsatisfactory', 'Approaching Basic'))
    math_inflated = sum(1 for r in students
                        if r.get('grade_math') is not None and float(r['grade_math']) >= 80
                        and r.get('math_level') in ('Unsatisfactory', 'Approaching Basic'))
    has_grade_ela = sum(1 for r in students if r.get('grade_ela') is not None)
    has_grade_math = sum(1 for r in students if r.get('grade_math') is not None)

    anet_ela = [float(r['anet_boy_ela']) for r in students if r.get('anet_boy_ela') is not None]
    anet_math = [float(r['anet_boy_math']) for r in students if r.get('anet_boy_math') is not None]
    mean_anet_ela = sum(anet_ela)/len(anet_ela) if anet_ela else 0
    mean_anet_math = sum(anet_math)/len(anet_math) if anet_math else 0

    grades_ela = [float(r['grade_ela']) for r in students if r.get('grade_ela') is not None]
    grades_math = [float(r['grade_math']) for r in students if r.get('grade_math') is not None]
    mean_grade_ela = sum(grades_ela)/len(grades_ela) if grades_ela else 0
    mean_grade_math = sum(grades_math)/len(grades_math) if grades_math else 0

    print(f"\n  {el_label} (n={n}):")
    print(f"    LEAP prof: ELA {100*ela_prof/n:.1f}%, Math {100*math_prof/n:.1f}%")
    print(f"    Mean anet BOY: ELA {mean_anet_ela:.1f}%, Math {mean_anet_math:.1f}%")
    print(f"    Mean course grade: ELA {mean_grade_ela:.1f}%, Math {mean_grade_math:.1f}%")
    print(f"    Grade inflation: ELA {ela_inflated}/{has_grade_ela} ({100*ela_inflated/max(has_grade_ela,1):.1f}%), Math {math_inflated}/{has_grade_math} ({100*math_inflated/max(has_grade_math,1):.1f}%)")

# Grade inflation by SPED and school
print("\n=== MATH GRADE INFLATION: SPED vs Regular BY SCHOOL ===")
for sch in ['Ashe', 'Green', 'Wheatley']:  # LHA excluded (no _full)
    for sped_label, sped_filter in [('SPED', lambda r: r.get('sped_class') == 'Special'),
                                      ('Reg', lambda r: r.get('sped_class') == 'Regular')]:
        students = [r for r in data if school_short(r.get('school','')) == sch and sped_filter(r)]
        has_grade = [r for r in students if r.get('grade_math') is not None]
        inflated = sum(1 for r in has_grade if float(r['grade_math']) >= 80 and r.get('math_level') in ('Unsatisfactory', 'Approaching Basic'))
        n = len(has_grade)
        if n > 0:
            print(f"  {sch} {sped_label}: {inflated}/{n} ({100*inflated/n:.1f}%) inflated")

# SPED gap in grade inflation
print("\n=== KEY METRIC: Gap between grade and LEAP for SPED ===")
sped = [r for r in data if r.get('sped_class') == 'Special']
reg = [r for r in data if r.get('sped_class') == 'Regular']

# For SPED: avg grade vs avg LEAP proficiency rate
sped_grade_math = [float(r['grade_math']) for r in sped if r.get('grade_math')]
sped_math_prof = sum(1 for r in sped if is_prof(r.get('math_level','')))
reg_grade_math = [float(r['grade_math']) for r in reg if r.get('grade_math')]
reg_math_prof = sum(1 for r in reg if is_prof(r.get('math_level','')))

if sped_grade_math:
    print(f"  SPED: Mean Math grade {sum(sped_grade_math)/len(sped_grade_math):.1f}%, LEAP Math prof {100*sped_math_prof/len(sped):.1f}% (gap: {sum(sped_grade_math)/len(sped_grade_math) - 100*sped_math_prof/len(sped):.1f}pp)")
if reg_grade_math:
    print(f"  Regular: Mean Math grade {sum(reg_grade_math)/len(reg_grade_math):.1f}%, LEAP Math prof {100*reg_math_prof/len(reg):.1f}% (gap: {sum(reg_grade_math)/len(reg_grade_math) - 100*reg_math_prof/len(reg):.1f}pp)")
