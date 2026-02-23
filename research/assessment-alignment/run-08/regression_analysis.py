"""
Run 8 - Multivariate Prediction Models for LEAP
Using scipy.stats for OLS regression (no sklearn available)
"""
import json
import numpy as np
from scipy import stats
import os

base = 'C:/Users/sshirey/bigquery-dashboards/research/assessment-alignment/run-08'

# Load master dataset
with open(f'{base}/master_dataset.json') as f:
    master = json.load(f)

print(f"Master dataset: {len(master)} students\n")

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def ols_regression(y, X, predictor_names):
    """
    OLS regression using numpy least squares.
    Returns dict with coefficients, R-squared, adj R-squared, p-values, etc.
    """
    n = len(y)
    k = X.shape[1]  # includes intercept

    # Solve via least squares
    beta, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)

    y_hat = X @ beta
    ss_res = np.sum((y - y_hat)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r_sq = 1 - ss_res / ss_tot
    adj_r_sq = 1 - (1 - r_sq) * (n - 1) / (n - k)

    # Standard errors
    mse = ss_res / (n - k)
    try:
        var_beta = mse * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(var_beta))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)

    # t-stats and p-values
    t_stats = beta / se
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-k))

    # RMSE and MAE
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(y - y_hat))

    result = {
        'n': n,
        'k': k - 1,  # predictors (not counting intercept)
        'r_sq': r_sq,
        'adj_r_sq': adj_r_sq,
        'rmse': rmse,
        'mae': mae,
        'intercept': beta[0],
        'intercept_se': se[0],
        'intercept_p': p_values[0],
        'predictors': [],
        'y_hat': y_hat,
        'residuals': y - y_hat
    }

    for i, name in enumerate(predictor_names):
        result['predictors'].append({
            'name': name,
            'coef': beta[i+1],
            'se': se[i+1],
            't': t_stats[i+1],
            'p': p_values[i+1]
        })

    return result


def get_complete_cases(data, outcome_col, predictor_cols):
    """
    Get arrays of y and X for complete cases only.
    Returns y (1d), X (2d with intercept), n_complete, predictor_names
    """
    rows = []
    for r in data:
        vals = [r[outcome_col]] + [r[c] for c in predictor_cols]
        if all(v is not None for v in vals):
            rows.append([float(v) for v in vals])

    if not rows:
        return None, None, 0, predictor_cols

    arr = np.array(rows)
    y = arr[:, 0]
    X_raw = arr[:, 1:]
    # Add intercept
    X = np.column_stack([np.ones(len(y)), X_raw])
    return y, X, len(y), predictor_cols


def train_test_split(y, X, train_frac=0.7, seed=42):
    """Simple random train/test split"""
    rng = np.random.RandomState(seed)
    n = len(y)
    idx = rng.permutation(n)
    split = int(n * train_frac)
    train_idx = idx[:split]
    test_idx = idx[split:]
    return y[train_idx], X[train_idx], y[test_idx], X[test_idx]


def evaluate_test_set(y_train, X_train, y_test, X_test):
    """Train on train set, predict on test set, return test R-sq, RMSE, MAE"""
    beta, _, _, _ = np.linalg.lstsq(X_train, y_train, rcond=None)
    y_hat_test = X_test @ beta
    ss_res = np.sum((y_test - y_hat_test)**2)
    ss_tot = np.sum((y_test - np.mean(y_test))**2)
    r_sq = 1 - ss_res / ss_tot
    rmse = np.sqrt(np.mean((y_test - y_hat_test)**2))
    mae = np.mean(np.abs(y_test - y_hat_test))
    return r_sq, rmse, mae


def format_model(result, model_name):
    """Pretty print a model result"""
    lines = [f"\n{'='*60}"]
    lines.append(f"MODEL: {model_name}")
    lines.append(f"n={result['n']}, predictors={result['k']}")
    lines.append(f"R²={result['r_sq']:.4f}, Adj R²={result['adj_r_sq']:.4f}, RMSE={result['rmse']:.1f}, MAE={result['mae']:.1f}")
    lines.append(f"Intercept: {result['intercept']:.3f} (SE={result['intercept_se']:.3f})")
    for p in result['predictors']:
        sig = '***' if p['p'] < 0.001 else '**' if p['p'] < 0.01 else '*' if p['p'] < 0.05 else ''
        lines.append(f"  {p['name']:30s}: b={p['coef']:.4f} (SE={p['se']:.4f}, t={p['t']:.2f}, p={p['p']:.4f}) {sig}")
    return '\n'.join(lines)


# ============================================================
# PART B: REGRESSION MODELS
# ============================================================

all_results = {}

# ---- ELA MODELS ----
print("=" * 70)
print("ELA PREDICTION MODELS")
print("=" * 70)

ela_models = [
    ("ELA-M1: anet ELA BOY only", ['anet_ela_boy']),
    ("ELA-M2: PM ELA only", ['pm_ela']),
    ("ELA-M3: anet ELA BOY + PM ELA", ['anet_ela_boy', 'pm_ela']),
    ("ELA-M4: anet ELA BOY + PM ELA + ORF BOY", ['anet_ela_boy', 'pm_ela', 'orf_boy']),
    ("ELA-M5: anet ELA BOY + PM ELA + ORF BOY + Grade ELA", ['anet_ela_boy', 'pm_ela', 'orf_boy', 'grade_ela']),
    ("ELA-M6: PM ELA + PM Science + PM Soc.Stu", ['pm_ela', 'pm_sci', 'pm_ss']),
]

for model_name, preds in ela_models:
    y, X, n, _ = get_complete_cases(master, 'ela_ss', preds)
    if n > 0:
        result = ols_regression(y, X, preds)
        all_results[model_name] = result
        print(format_model(result, model_name))
    else:
        print(f"\n{model_name}: NO COMPLETE CASES")

# ---- MATH MODELS ----
print("\n" + "=" * 70)
print("MATH PREDICTION MODELS")
print("=" * 70)

math_models = [
    ("Math-M1: anet Math BOY only", ['anet_math_boy']),
    ("Math-M2: PM Math only", ['pm_math']),
    ("Math-M3: anet Math BOY + PM Math", ['anet_math_boy', 'pm_math']),
    ("Math-M4: anet Math BOY + PM Math + MAP Math BOY %ile", ['anet_math_boy', 'pm_math', 'map_math_boy_pctile']),
    ("Math-M5: anet Math BOY + PM Math + Grade Math", ['anet_math_boy', 'pm_math', 'grade_math']),
    ("Math-M6: PM Math + PM Science", ['pm_math', 'pm_sci']),
]

for model_name, preds in math_models:
    y, X, n, _ = get_complete_cases(master, 'math_ss', preds)
    if n > 0:
        result = ols_regression(y, X, preds)
        all_results[model_name] = result
        print(format_model(result, model_name))
    else:
        print(f"\n{model_name}: NO COMPLETE CASES")

# ---- SCIENCE MODELS ----
print("\n" + "=" * 70)
print("SCIENCE PREDICTION MODELS")
print("=" * 70)

sci_models = [
    ("Sci-M1: PM Science only", ['pm_sci']),
    ("Sci-M2: anet ELA BOY + PM Science", ['anet_ela_boy', 'pm_sci']),
    ("Sci-M3: PM Science + PM ELA + PM Math", ['pm_sci', 'pm_ela', 'pm_math']),
    ("Sci-M4: PM Science + anet ELA BOY + ORF BOY", ['pm_sci', 'anet_ela_boy', 'orf_boy']),
]

for model_name, preds in sci_models:
    y, X, n, _ = get_complete_cases(master, 'sci_ss', preds)
    if n > 0:
        result = ols_regression(y, X, preds)
        all_results[model_name] = result
        print(format_model(result, model_name))
    else:
        print(f"\n{model_name}: NO COMPLETE CASES")

# ---- SOCIAL STUDIES MODELS ----
print("\n" + "=" * 70)
print("SOCIAL STUDIES PREDICTION MODELS")
print("=" * 70)

ss_models = [
    ("SS-M1: PM Soc.Stu only", ['pm_ss']),
    ("SS-M2: anet ELA BOY + PM Soc.Stu", ['anet_ela_boy', 'pm_ss']),
    ("SS-M3: PM Soc.Stu + PM ELA + PM Science", ['pm_ss', 'pm_ela', 'pm_sci']),
]

for model_name, preds in ss_models:
    y, X, n, _ = get_complete_cases(master, 'ss_ss', preds)
    if n > 0:
        result = ols_regression(y, X, preds)
        all_results[model_name] = result
        print(format_model(result, model_name))
    else:
        print(f"\n{model_name}: NO COMPLETE CASES")


# ============================================================
# PART B (cont): TRAIN/TEST VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("TRAIN/TEST VALIDATION (70/30 x 5 splits)")
print("=" * 70)

# Best models per subject (will determine from results)
best_models = {
    'ELA': ("ELA-M5: anet ELA BOY + PM ELA + ORF BOY + Grade ELA", 'ela_ss', ['anet_ela_boy', 'pm_ela', 'orf_boy', 'grade_ela']),
    'Math': ("Math-M4: anet Math BOY + PM Math + MAP Math BOY %ile", 'math_ss', ['anet_math_boy', 'pm_math', 'map_math_boy_pctile']),
    'Science': ("Sci-M3: PM Science + PM ELA + PM Math", 'sci_ss', ['pm_sci', 'pm_ela', 'pm_math']),
    'SocStu': ("SS-M3: PM Soc.Stu + PM ELA + PM Science", 'ss_ss', ['pm_ss', 'pm_ela', 'pm_sci']),
}

# Also validate the most practical models (high coverage)
practical_models = {
    'ELA-practical': ("ELA-M3: anet ELA BOY + PM ELA", 'ela_ss', ['anet_ela_boy', 'pm_ela']),
    'Math-practical': ("Math-M3: anet Math BOY + PM Math", 'math_ss', ['anet_math_boy', 'pm_math']),
}

validation_results = {}

for label, (model_name, outcome, preds) in {**best_models, **practical_models}.items():
    y, X, n, _ = get_complete_cases(master, outcome, preds)
    if n < 50:
        print(f"\n{label}: insufficient data (n={n})")
        continue

    # 5-fold random split validation
    test_rsqs = []
    test_rmses = []
    test_maes = []
    for seed in [42, 123, 456, 789, 1010]:
        y_tr, X_tr, y_te, X_te = train_test_split(y, X, 0.7, seed)
        r2, rmse, mae = evaluate_test_set(y_tr, X_tr, y_te, X_te)
        test_rsqs.append(r2)
        test_rmses.append(rmse)
        test_maes.append(mae)

    # Training set R-sq (full model)
    result = ols_regression(y, X, preds)
    train_rsq = result['r_sq']

    vr = {
        'train_rsq': train_rsq,
        'test_rsq_mean': np.mean(test_rsqs),
        'test_rsq_sd': np.std(test_rsqs),
        'test_rmse_mean': np.mean(test_rmses),
        'test_rmse_sd': np.std(test_rmses),
        'test_mae_mean': np.mean(test_maes),
        'test_mae_sd': np.std(test_maes),
        'n': n,
        'model_name': model_name,
        'preds': preds
    }
    validation_results[label] = vr

    print(f"\n{label} ({model_name})")
    print(f"  n={n}")
    print(f"  Train R²: {train_rsq:.4f}")
    print(f"  Test R²:  {np.mean(test_rsqs):.4f} ± {np.std(test_rsqs):.4f}")
    print(f"  Test RMSE: {np.mean(test_rmses):.1f} ± {np.std(test_rmses):.1f}")
    print(f"  Test MAE:  {np.mean(test_maes):.1f} ± {np.std(test_maes):.1f}")
    print(f"  Overfit check: Train-Test R² gap = {train_rsq - np.mean(test_rsqs):.4f}")


# ============================================================
# PART C: RISK TIERS
# ============================================================
print("\n" + "=" * 70)
print("RISK TIER CALIBRATION")
print("=" * 70)

# First, determine LEAP cut scores from data
ach_levels = {'Unsatisfactory': 1, 'Approaching Basic': 2, 'Basic': 3, 'Mastery': 4, 'Advanced': 5}

# Analyze LEAP cut scores empirically
for subj, ss_col, ach_col in [('ELA','ela_ss','ela_ach'), ('Math','math_ss','math_ach'),
                               ('Science','sci_ss','sci_ach'), ('SocStu','ss_ss','ss_ach')]:
    print(f"\n{subj} Scale Score by Achievement Level:")
    level_scores = {}
    for r in master:
        if r[ss_col] is not None and r[ach_col] and r[ach_col].strip():
            ach = r[ach_col].strip()
            if ach in ach_levels:
                level_scores.setdefault(ach, []).append(r[ss_col])

    for level in ['Unsatisfactory','Approaching Basic','Basic','Mastery','Advanced']:
        if level in level_scores:
            scores = level_scores[level]
            print(f"  {level:20s}: n={len(scores):4d}, min={min(scores):5.0f}, max={max(scores):5.0f}, mean={np.mean(scores):6.1f}")


# Use the practical models for risk tiers (highest coverage)
# ELA: anet ELA BOY + PM ELA (n~1750)
# Math: anet Math BOY + PM Math (n~1700)
# For Sci/SS: PM only (n~1876-1881)

print("\n\n--- RISK TIER ANALYSIS ---")

# Helper: compute risk tiers
def compute_risk_tiers(data, outcome_col, ach_col, preds, subject_label, cut_scores):
    """
    cut_scores: dict mapping tier name to (min_predicted_ss, max_predicted_ss)
    """
    y, X, n, _ = get_complete_cases(data, outcome_col, preds)
    if n == 0:
        return None

    result = ols_regression(y, X, preds)
    y_hat = result['y_hat']

    # Get actual achievement levels for these students
    complete_rows = [r for r in data if all(r[c] is not None for c in [outcome_col] + preds)]

    tiers = {}
    for i, row in enumerate(complete_rows):
        pred_ss = y_hat[i]
        actual_ach = row[ach_col]
        actual_ss = row[outcome_col]

        # Assign predicted tier
        if pred_ss < cut_scores['Crisis']:
            tier = 'Crisis'
        elif pred_ss < cut_scores['Intervention']:
            tier = 'Intervention'
        elif pred_ss < cut_scores['Watch']:
            tier = 'Watch'
        else:
            tier = 'On Track'

        actual_prof = actual_ach in ('Mastery', 'Advanced') if actual_ach else False
        actual_unsat = actual_ach == 'Unsatisfactory' if actual_ach else False
        actual_unsat_ab = actual_ach in ('Unsatisfactory', 'Approaching Basic') if actual_ach else False

        tiers.setdefault(tier, {'n': 0, 'prof': 0, 'unsat': 0, 'unsat_ab': 0})
        tiers[tier]['n'] += 1
        if actual_prof:
            tiers[tier]['prof'] += 1
        if actual_unsat:
            tiers[tier]['unsat'] += 1
        if actual_unsat_ab:
            tiers[tier]['unsat_ab'] += 1

    print(f"\n{subject_label} Risk Tiers (n={n})")
    print(f"  {'Tier':15s} {'n':>5s} {'Prof%':>6s} {'U%':>6s} {'U+AB%':>6s}")
    total_unsat = sum(t['unsat'] for t in tiers.values())
    total_prof = sum(t['prof'] for t in tiers.values())
    caught = 0
    for tier_name in ['Crisis', 'Intervention', 'Watch', 'On Track']:
        t = tiers.get(tier_name, {'n': 0, 'prof': 0, 'unsat': 0, 'unsat_ab': 0})
        if t['n'] > 0:
            prof_pct = t['prof']/t['n']*100
            unsat_pct = t['unsat']/t['n']*100
            unsat_ab_pct = t['unsat_ab']/t['n']*100
        else:
            prof_pct = unsat_pct = unsat_ab_pct = 0
        if tier_name in ('Crisis', 'Intervention'):
            caught += t['unsat']
        print(f"  {tier_name:15s} {t['n']:5d} {prof_pct:5.1f}% {unsat_pct:5.1f}% {unsat_ab_pct:5.1f}%")

    if total_unsat > 0:
        sensitivity = caught / total_unsat * 100
        print(f"  Sensitivity (Crisis+Interv catches U): {sensitivity:.1f}% ({caught}/{total_unsat})")

    false_pos = sum(tiers.get(t, {}).get('prof', 0) for t in ['Crisis', 'Intervention'])
    flagged = sum(tiers.get(t, {}).get('n', 0) for t in ['Crisis', 'Intervention'])
    if flagged > 0:
        fpr = false_pos / flagged * 100
        print(f"  False positive rate (prof in Crisis+Interv): {fpr:.1f}% ({false_pos}/{flagged})")

    return tiers, result

# Determine cut scores from data
# Let's use the midpoints between achievement level ranges
print("\nDetermining LEAP cut scores from data...")
for subj, ss_col, ach_col in [('ELA','ela_ss','ela_ach'), ('Math','math_ss','math_ach'),
                               ('Science','sci_ss','sci_ach'), ('SocStu','ss_ss','ss_ach')]:
    boundaries = {}
    level_data = {}
    for r in master:
        if r[ss_col] is not None and r[ach_col] and r[ach_col].strip() in ach_levels:
            level_data.setdefault(r[ach_col].strip(), []).append(r[ss_col])

    # Find boundaries as max of lower level / min of upper level midpoint
    levels_ordered = ['Unsatisfactory','Approaching Basic','Basic','Mastery','Advanced']
    for i in range(len(levels_ordered)-1):
        lower = levels_ordered[i]
        upper = levels_ordered[i+1]
        if lower in level_data and upper in level_data:
            max_lower = max(level_data[lower])
            min_upper = min(level_data[upper])
            midpoint = (max_lower + min_upper) / 2
            boundaries[f"{lower}->{upper}"] = midpoint
            print(f"  {subj} {lower}->{upper}: max_low={max_lower}, min_high={min_upper}, cut={midpoint:.0f}")

# Based on LA LEAP documentation and data patterns, use standard cut scores:
# These are grade-specific in reality, but we'll use approximate network-level cuts
# from the empirical data above

# Let me compute the actual boundaries more carefully
print("\n\nEmpirical cut scores (min score at each level):")
cut_scores_by_subj = {}
for subj, ss_col, ach_col in [('ELA','ela_ss','ela_ach'), ('Math','math_ss','math_ach'),
                               ('Science','sci_ss','sci_ach'), ('SocStu','ss_ss','ss_ach')]:
    levels_ordered = ['Unsatisfactory','Approaching Basic','Basic','Mastery','Advanced']
    cuts = {}
    for level in levels_ordered:
        scores = [r[ss_col] for r in master if r[ach_col] and r[ach_col].strip() == level and r[ss_col] is not None]
        if scores:
            cuts[level] = {'min': min(scores), 'max': max(scores), 'n': len(scores)}
            print(f"  {subj} {level:20s}: min={min(scores):4.0f}, max={max(scores):4.0f}, n={len(scores)}")
    cut_scores_by_subj[subj] = cuts

# For risk tiers, map predicted score to tier using the min-score-at-level as boundaries
# Crisis = predicted < min(Approaching Basic)
# Intervention = predicted < min(Basic)
# Watch = predicted < min(Mastery)
# On Track = predicted >= min(Mastery)

risk_cuts = {}
for subj in ['ELA', 'Math', 'Science', 'SocStu']:
    cuts = cut_scores_by_subj[subj]
    risk_cuts[subj] = {
        'Crisis': cuts.get('Approaching Basic', {}).get('min', 725),
        'Intervention': cuts.get('Basic', {}).get('min', 750),
        'Watch': cuts.get('Mastery', {}).get('min', 775),
    }
    print(f"\n{subj} risk tier cuts: Crisis<{risk_cuts[subj]['Crisis']}, Intervention<{risk_cuts[subj]['Intervention']}, Watch<{risk_cuts[subj]['Watch']}")

# Run risk tier analysis
tier_results = {}

# ELA: practical model (anet BOY + PM ELA)
ela_tiers = compute_risk_tiers(master, 'ela_ss', 'ela_ach',
    ['anet_ela_boy', 'pm_ela'], 'ELA (anet BOY + PM)', risk_cuts['ELA'])
if ela_tiers:
    tier_results['ELA'] = ela_tiers

# Math: practical model (anet Math BOY + PM Math)
math_tiers = compute_risk_tiers(master, 'math_ss', 'math_ach',
    ['anet_math_boy', 'pm_math'], 'Math (anet BOY + PM)', risk_cuts['Math'])
if math_tiers:
    tier_results['Math'] = math_tiers

# Science: PM only
sci_tiers = compute_risk_tiers(master, 'sci_ss', 'sci_ach',
    ['pm_sci'], 'Science (PM only)', risk_cuts['Science'])
if sci_tiers:
    tier_results['Science'] = sci_tiers

# Social Studies: PM only
ss_tiers = compute_risk_tiers(master, 'ss_ss', 'ss_ach',
    ['pm_ss'], 'Soc.Stu (PM only)', risk_cuts['SocStu'])
if ss_tiers:
    tier_results['SocStu'] = ss_tiers


# ============================================================
# COMPARISON: Run 5 simple tiers vs model-based tiers
# ============================================================
print("\n" + "=" * 70)
print("COMPARISON: Run 5 simple tiers vs model-based tiers")
print("=" * 70)

# Run 5 used anet BOY alone with fixed thresholds: <20% Crisis, 20-30% Intervention, 30-50% Watch, >=50% On Track
print("\nRun 5 tiers (anet BOY only):")
for subj, anet_col, ss_col, ach_col in [('ELA','anet_ela_boy','ela_ss','ela_ach'),
                                          ('Math','anet_math_boy','math_ss','math_ach')]:
    tiers_simple = {'Crisis': {'n':0,'prof':0,'unsat':0}, 'Intervention': {'n':0,'prof':0,'unsat':0},
                    'Watch': {'n':0,'prof':0,'unsat':0}, 'On Track': {'n':0,'prof':0,'unsat':0}}
    total_u = 0
    for r in master:
        if r[anet_col] is not None and r[ss_col] is not None and r[ach_col]:
            anet_pct = r[anet_col]
            if anet_pct < 20:
                tier = 'Crisis'
            elif anet_pct < 30:
                tier = 'Intervention'
            elif anet_pct < 50:
                tier = 'Watch'
            else:
                tier = 'On Track'

            tiers_simple[tier]['n'] += 1
            if r[ach_col] in ('Mastery', 'Advanced'):
                tiers_simple[tier]['prof'] += 1
            if r[ach_col] == 'Unsatisfactory':
                tiers_simple[tier]['unsat'] += 1
                total_u += 1

    print(f"\n  {subj} (Run 5 simple anet BOY tiers):")
    caught_simple = 0
    for t_name in ['Crisis', 'Intervention', 'Watch', 'On Track']:
        t = tiers_simple[t_name]
        if t['n'] > 0:
            print(f"    {t_name:15s}: n={t['n']:4d}, Prof%={t['prof']/t['n']*100:5.1f}%, U%={t['unsat']/t['n']*100:5.1f}%")
        if t_name in ('Crisis', 'Intervention'):
            caught_simple += t['unsat']
    if total_u > 0:
        print(f"    Sensitivity: {caught_simple/total_u*100:.1f}% ({caught_simple}/{total_u})")


# ============================================================
# SCHOOL-LEVEL AND GRADE-LEVEL PERFORMANCE
# ============================================================
print("\n" + "=" * 70)
print("SCHOOL-LEVEL MODEL PERFORMANCE")
print("=" * 70)

# School name mapping
school_short = {
    'Arthur Ashe Charter School': 'Ashe',
    'Samuel J. Green Charter School': 'Green',
    'Langston Hughes Charter Academy': 'LHA',
    'Phillis Wheatley Community School': 'Wheatley'
}

for subj, ss_col, preds in [('ELA', 'ela_ss', ['anet_ela_boy', 'pm_ela']),
                              ('Math', 'math_ss', ['anet_math_boy', 'pm_math'])]:
    print(f"\n{subj} - R² by school:")
    for school_full, school_abbrev in school_short.items():
        school_data = [r for r in master if r['school'] == school_full]
        y, X, n, _ = get_complete_cases(school_data, ss_col, preds)
        if n > 30:
            result = ols_regression(y, X, preds)
            print(f"  {school_abbrev:10s}: R²={result['r_sq']:.4f}, n={n}")

print("\n" + "=" * 70)
print("GRADE-LEVEL MODEL PERFORMANCE")
print("=" * 70)

for subj, ss_col, preds in [('ELA', 'ela_ss', ['anet_ela_boy', 'pm_ela']),
                              ('Math', 'math_ss', ['anet_math_boy', 'pm_math'])]:
    print(f"\n{subj} - R² by grade:")
    for grade in [3, 4, 5, 6, 7, 8]:
        grade_data = [r for r in master if r['grade'] == grade]
        y, X, n, _ = get_complete_cases(grade_data, ss_col, preds)
        if n > 30:
            result = ols_regression(y, X, preds)
            print(f"  Grade {grade}: R²={result['r_sq']:.4f}, n={n}")


# ============================================================
# SEPTEMBER vs MID-YEAR COMPARISON
# ============================================================
print("\n" + "=" * 70)
print("SEPTEMBER vs MID-YEAR COMPARISON")
print("=" * 70)

for subj, ss_col in [('ELA', 'ela_ss'), ('Math', 'math_ss')]:
    print(f"\n{subj}:")
    sept_preds_list = [
        (f"anet {subj} BOY only", [f'anet_{subj.lower()}_boy']),
        (f"MAP {subj} BOY %ile", [f'map_{subj.lower()}_boy_pctile']),
    ]
    if subj == 'ELA':
        sept_preds_list.append(("anet ELA BOY + MAP ELA BOY", ['anet_ela_boy', 'map_ela_boy_pctile']))
        sept_preds_list.append(("anet ELA BOY + MAP ELA BOY + ORF BOY", ['anet_ela_boy', 'map_ela_boy_pctile', 'orf_boy']))

    midyear_list = [
        (f"PM {subj}", [f'pm_{subj.lower()}']),
        (f"anet {subj} BOY + PM {subj}", [f'anet_{subj.lower()}_boy', f'pm_{subj.lower()}']),
        (f"anet {subj} MOY + PM {subj}", [f'anet_{subj.lower()}_moy', f'pm_{subj.lower()}']),
    ]

    print("  September predictors:")
    for name, preds in sept_preds_list:
        y, X, n, _ = get_complete_cases(master, ss_col, preds)
        if n > 50:
            result = ols_regression(y, X, preds)
            print(f"    {name:45s}: R²={result['r_sq']:.4f} (n={n})")

    print("  Mid-year predictors:")
    for name, preds in midyear_list:
        y, X, n, _ = get_complete_cases(master, ss_col, preds)
        if n > 50:
            result = ols_regression(y, X, preds)
            print(f"    {name:45s}: R²={result['r_sq']:.4f} (n={n})")


# ============================================================
# DIMINISHING RETURNS
# ============================================================
print("\n" + "=" * 70)
print("DIMINISHING RETURNS ANALYSIS")
print("=" * 70)

for subj, ss_col, pred_sequence in [
    ('ELA', 'ela_ss', [
        ('PM ELA', ['pm_ela']),
        ('+ anet ELA BOY', ['pm_ela', 'anet_ela_boy']),
        ('+ ORF BOY', ['pm_ela', 'anet_ela_boy', 'orf_boy']),
        ('+ Grade ELA', ['pm_ela', 'anet_ela_boy', 'orf_boy', 'grade_ela']),
        ('+ PM Science', ['pm_ela', 'anet_ela_boy', 'orf_boy', 'grade_ela', 'pm_sci']),
        ('+ PM Soc.Stu', ['pm_ela', 'anet_ela_boy', 'orf_boy', 'grade_ela', 'pm_sci', 'pm_ss']),
    ]),
    ('Math', 'math_ss', [
        ('PM Math', ['pm_math']),
        ('+ anet Math BOY', ['pm_math', 'anet_math_boy']),
        ('+ Grade Math', ['pm_math', 'anet_math_boy', 'grade_math']),
        ('+ PM Science', ['pm_math', 'anet_math_boy', 'grade_math', 'pm_sci']),
    ]),
]:
    print(f"\n{subj} diminishing returns:")
    prev_rsq = 0
    for name, preds in pred_sequence:
        y, X, n, _ = get_complete_cases(master, ss_col, preds)
        if n > 50:
            result = ols_regression(y, X, preds)
            delta = result['r_sq'] - prev_rsq
            marker = " <-- DIMINISHING" if delta < 0.01 and prev_rsq > 0 else ""
            print(f"  {name:35s}: R²={result['r_sq']:.4f} (Δ={delta:+.4f}, n={n}){marker}")
            prev_rsq = result['r_sq']


# ============================================================
# SAVE ALL RESULTS FOR HTML GENERATION
# ============================================================
print("\n\nSaving results...")

# Convert results to serializable format
serializable = {}
for key, result in all_results.items():
    serializable[key] = {
        'n': result['n'],
        'k': result['k'],
        'r_sq': result['r_sq'],
        'adj_r_sq': result['adj_r_sq'],
        'rmse': result['rmse'],
        'mae': result['mae'],
        'intercept': result['intercept'],
        'intercept_se': float(result['intercept_se']),
        'intercept_p': float(result['intercept_p']),
        'predictors': result['predictors']
    }

output = {
    'models': serializable,
    'validation': {k: {kk: (vv if not isinstance(vv, list) else vv) for kk, vv in v.items()} for k, v in validation_results.items()},
    'risk_cuts': risk_cuts
}

with open(f'{base}/regression_results.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

print("Done!")
