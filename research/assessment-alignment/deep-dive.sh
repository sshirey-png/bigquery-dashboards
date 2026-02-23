#!/bin/bash
# =============================================================================
# Assessment Alignment Deep Dive - 9-Run Research Driver
# FirstLine Schools | February 2026
#
# Usage: bash deep-dive.sh [run_number]
#   bash deep-dive.sh 1    # Run 1: Schema Audit
#   bash deep-dive.sh 2    # Run 2: Internal Assessment Baseline
#   bash deep-dive.sh 3    # Run 3: LEAP State Test Patterns
#   bash deep-dive.sh 4    # Run 4: Concordance Analysis
#   bash deep-dive.sh 5    # Run 5: Synthesis & Predictive Model
#   bash deep-dive.sh 6    # Run 6: Cross-Subject Correlations & Standards Drill-Down
#   bash deep-dive.sh 7    # Run 7: PM Full-Subject, Fluency/ORF, & Cross-Year Validation
#   bash deep-dive.sh 8    # Run 8: Multivariate Prediction Model & Operationalization
#   bash deep-dive.sh 9    # Run 9: PM Standards-Level Diagnostic Analysis
# =============================================================================
set -euo pipefail

RUN_NUM="${1:-1}"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESEARCH_DIR="$PROJECT_DIR/research/assessment-alignment"
LEARNINGS="$RESEARCH_DIR/learnings.md"
PERSONA="$PROJECT_DIR/research/analyst-profile.md"
DATA_DICT="$PROJECT_DIR/data_dictionary.yaml"
OUTPUT_DIR="$RESEARCH_DIR/run-$(printf '%02d' "$RUN_NUM")"
TODAY=$(date +%Y-%m-%d)

# Lock file
LOCK_FILE="/tmp/fls-assessment-deep-dive.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Lock file exists at $LOCK_FILE. Previous run may still be active."
    echo "If the previous run crashed, delete the lock file manually: rm $LOCK_FILE"
    exit 1
fi
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "============================================"
echo "Assessment Alignment Deep Dive - Run $RUN_NUM of 9"
echo "Date: $TODAY"
echo "Output: $OUTPUT_DIR"
echo "============================================"

# Read accumulated knowledge
PRIOR=""
if [ -f "$LEARNINGS" ]; then
    PRIOR=$(cat "$LEARNINGS")
fi

# Read persona
ANALYST=""
if [ -f "$PERSONA" ]; then
    ANALYST=$(cat "$PERSONA")
fi

# Read data dictionary (first 200 lines -- join keys and gotchas section)
DICT_HEADER=""
if [ -f "$DATA_DICT" ]; then
    DICT_HEADER=$(head -65 "$DATA_DICT")
fi

# Run-specific prompts
case $RUN_NUM in
1)
    ASSIGNMENT="## Run 1 of 5: Schema Audit & Data Quality

Your job is to understand the ACTUAL structure of every assessment table that will be used in this study. Do not assume anything from the data dictionary -- verify everything with queries.

### Tasks:
1. **Query the schema** of these key tables (SELECT * LIMIT 5 for each):
   - \`fls-data-warehouse.leap.399001LEAPData24_25\` (and check 399002, 399004)
   - \`fls-data-warehouse.anet.ela_boy_25_26\` and \`math_boy_25_26\`
   - \`fls-data-warehouse.anet.ela_moy_25_26\` and \`math_moy_25_26\`
   - \`fls-data-warehouse.map.25_26_boy\` and \`25_26_moy\`
   - \`fls-data-warehouse.performance_matters.results_by_test\` and \`results_raw\`
   - \`fls-data-warehouse.grades.current_grades\` and \`simple_gpas\`
   - \`fls-data-warehouse.student_rosters.student_roster\`

2. **Document the actual column names and types** for student ID, school, grade, subject, score, and achievement level in each table.

3. **Test join paths**: Can you join LEAP to anet on LASID? On Student_Number? What is the match rate? Do the same for MAP, grades, and performance matters.

4. **Count unique students** in each assessment system for 2024-2025 school year. How many students have data in multiple systems?

5. **Map school names/codes** across systems. What does school 399001 map to in the anet table? In grades? Build a lookup.

6. **Document every gotcha** you find: NULL patterns, unexpected values, type mismatches, missing data.

### Output:
- Write a README.md summarizing your findings
- Build an HTML artifact showing the coverage matrix (which students have data in which systems)
- Append ALL findings to the learnings file under '## Run 1 - Schema Audit'"
    ;;
2)
    ASSIGNMENT="## Run 2 of 5: Internal Assessment Baseline

You now know the schemas and join paths from Run 1. Use that knowledge.

### Tasks:
1. **anet interim results**: For 2024-2025 (or 2025-2026 if available), what are the score distributions by school, grade, and subject? What proficiency levels exist and what are the cut scores? How do BOY and MOY compare -- what is the growth pattern?

2. **MAP (NWEA) results**: For current year, what are the RIT score distributions? What percentile bands are students in? How do BOY and MOY RIT scores compare? What is the typical growth?

3. **Performance Matters**: What tests are in the system? What do scores look like? How does completion rate vary by school?

4. **Course grades vs assessment scores**: For students with both grades data and anet/MAP data, what is the correlation? Are there students with high grades but low assessment scores (grade inflation signal)?

5. **Break everything down by school.** Are there systematic differences in assessment patterns across FirstLine schools?

### Output:
- Build an HTML artifact showing internal assessment distributions by school
- Include a concordance preview: where anet and MAP agree/disagree
- Append findings to learnings file under '## Run 2 - Internal Assessment Baseline'"
    ;;
3)
    ASSIGNMENT="## Run 3 of 5: LEAP State Test Patterns

Focus entirely on LEAP data and what it tells us about student performance on the state test.

### Tasks:
1. **LEAP score distributions** for 2023-2024 (most recent complete year with results). Break down by school, grade, subject. What percentage of students are at each achievement level?

2. **LEAP trends**: Compare 2022-2023 to 2023-2024. Are schools improving? Which grades/subjects show the most change?

3. **Bottom 25th percentile** (sps.24_25_bottom_25): Who are these students? What schools/grades are they concentrated in? What does their demographic profile look like?

4. **Subject patterns**: Is ELA or Math stronger? Does Science show different patterns? Are there grade levels where performance drops off sharply?

5. **LEAP Connect**: What students are in LEAP Connect (alternate assessment)? How many? What schools?

6. **Cross-reference with the internal assessment data from Run 2**: For students who took LEAP in 23-24, what did their internal assessments look like in the same year or the prior year? This is the setup for Run 4's concordance analysis.

### Output:
- Build an HTML artifact showing LEAP achievement distributions by school and subject
- Include year-over-year trend visualization
- Append findings to learnings file under '## Run 3 - LEAP State Test Patterns'"
    ;;
4)
    ASSIGNMENT="## Run 4 of 5: Concordance Analysis

This is the core analytical run. You have internal assessment data (Run 2) and LEAP data (Run 3). Now connect them.

### Tasks:
1. **Match students across systems**: For students who took LEAP in 2023-2024, find their internal assessment scores (anet, MAP, grades) from the same school year or the immediately prior testing window. Report match rates.

2. **Concordance rates**: What percentage of the time do internal assessments and LEAP agree on whether a student is proficient? Break this down:
   - anet proficient + LEAP Mastery/Advanced = TRUE POSITIVE
   - anet proficient + LEAP Below Basic = FALSE POSITIVE (grade inflation / assessment misalignment)
   - anet not proficient + LEAP Mastery = FALSE NEGATIVE (assessment underestimates student)
   - anet not proficient + LEAP Below Basic = TRUE NEGATIVE
   Do the same for MAP percentiles and course grades.

3. **Which internal assessment is the best predictor of LEAP?** Calculate correlation coefficients between each internal measure and LEAP scale scores. Report by subject.

4. **The blind spots**: Which students are flagged as at-risk by one system but not another? How many students are getting A's and B's in class but scoring Unsatisfactory/Approaching Basic on LEAP?

5. **School-level variation**: Does the concordance rate differ by school? Is one school's grading more aligned with LEAP than another's?

### Output:
- Build an HTML artifact with concordance matrices and scatter plots
- Highlight the false positive population (high grades, low LEAP) as the primary actionable finding
- Append findings to learnings file under '## Run 4 - Concordance Analysis'"
    ;;
5)
    ASSIGNMENT="## Run 5 of 5: Synthesis & Predictive Model

You have 4 runs of accumulated knowledge. Synthesize everything.

### Tasks:
1. **Build a prediction framework**: Using all available internal assessment data, which combination of factors best predicts LEAP performance? Rank the predictors by effect size.

2. **Identify the highest-leverage intervention point**: Based on the concordance analysis, where is the biggest gap between what internal assessments say and what LEAP shows? That gap represents students who COULD be helped if identified earlier.

3. **Create student risk tiers**: Using the data from Runs 2-4, define 3-4 risk tiers (e.g., On Track, Watch, Intervention Needed, Crisis). How many students fall into each tier? What does each tier's LEAP outcome look like historically?

4. **School-specific recommendations**: For each FirstLine school, what are the 2-3 most actionable findings? Where is their internal assessment system most and least aligned with state standards?

5. **Document what this study CANNOT answer**: What questions remain? What data would be needed? What are the limitations of this analysis?

6. **Write the executive summary**: 5-7 bullet points that a superintendent could read in 2 minutes and act on.

### Output:
- Build a comprehensive HTML synthesis artifact -- this is the capstone deliverable
- Include the risk tier framework, the prediction model, and school-specific findings
- Write a complete final section in the learnings file under '## Run 5 - Synthesis'
- End with 'Questions for Future Studies' section"
    ;;
6)
    ASSIGNMENT="## Run 6 of 6: Cross-Subject Correlations & Standards-Level Drill-Down

Science and Social Studies have no internal assessment system (anet/MAP cover only ELA and Math), yet LEAP tests both. This run explores whether ELA/Math scores can serve as early warnings for Science/SS, and digs into standards-level granularity to identify which anet domains predict which LEAP subscores.

### Part A: Cross-Subject Correlations

1. **LEAP 4x4 correlation matrix**: Build a correlation matrix of LEAP scale scores across all four subjects (ELA, Math, Science, Social Studies) for all ~1,890 students. Use the regular LEAP tables for all 4 schools (399001-399005). The scale score columns are: ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialStudiesScaleScore. CAST to FLOAT64 as needed (some are STRING).

2. **Hypothesis test**: Does ELA predict Science more strongly than Math predicts Science? Compare r(ELA,Science) vs r(Math,Science) using Fisher's z-transformation for statistical significance. Report the z-statistic and p-value.

3. **LEAP reporting category subscores**: The LEAP _full tables (399001LEAPDataFull24_25, etc.) have granular subscore columns. IMPORTANT: These subscore columns are STRING type — query a LIMIT 5 sample first to see actual values before attempting correlations. If values are categorical (e.g., 'Strong', 'Weak'), convert to ordinal. If numeric strings, SAFE_CAST to FLOAT64. Correlate ELA subscores (ReadingInformationalText, ReadingLiteraryText, WritingComposing, etc.) with Science subscores. NOTE: _full tables may only exist for 3 of 4 schools (399001, 399002, 399004) — verify whether 399005LEAPDataFull24_25 exists before querying.

4. **anet → LEAP cross-subject prediction**: Correlate anet ELA scores with LEAP Science and Social Studies scale scores. Correlate anet Math scores with LEAP Science and Social Studies. Can anet ELA serve as a Science early warning?

5. **Performance Matters Science/SS data**: Check \`fls-data-warehouse.performance_matters.results_raw\` for Science and Social Studies content. The \`LA_State_Standard\` column has standards with points_earned/points_possible. Filter for Science and Social Studies standards. This is the only internal system that may have Science/SS assessment data.

6. **School and grade breakdowns**: Break down all cross-subject correlations by school (Ashe, Green, LHA, Wheatley) and by grade level. Are there schools or grades where ELA is a stronger/weaker proxy for Science?

### Part B: Standards-Level Drill-Down

7. **Document the anet domain taxonomy**: Query distinct values of \`domain\` and \`cc_standard_code\` from the anet ELA and Math tables (ela_boy_25_26, ela_moy_25_26, math_boy_25_26, math_moy_25_26). IMPORTANT: Column names with \`&\` characters need backtick quoting in BigQuery (e.g., \\\`Reading: Literature & Informational\\\`). Count how many items and students per domain.

8. **Aggregate anet scores by domain**: For each student, compute domain-level proficiency as SUM(points_received) / SUM(points_possible) GROUP BY student, domain. Use the latest available window (MOY 25-26 preferred, BOY 25-26 as fallback).

9. **Correlate anet domains with LEAP subscores**: Build a heatmap matrix where rows are anet domains and columns are LEAP reporting category subscores. Each cell is the Pearson correlation. Use 2023-2024 anet and LEAP data if available, otherwise use the cross-year approach from Run 4 (25-26 anet → 23-24 LEAP).

10. **Rank domains by predictive power**: Which anet domains are the strongest predictors of LEAP scale scores? Which are weakest? Report R-squared values and rank order.

### Output:
- Create a self-contained HTML artifact at \`$OUTPUT_DIR/cross-subject-standards.html\` with:
  - Heat-mapped 4x4 LEAP cross-subject correlation matrix
  - Hypothesis test verdict: \"Reading predicts Science [more/less/equally] well compared to Math\" with Fisher z p-value
  - anet domain → LEAP subscore correlation heatmap
  - Most/least predictive domains ranking table
  - School-level and grade-level breakdowns
- Append ALL findings to the learnings file under '## Run 6 - Cross-Subject & Standards Drill-Down'"
    ;;
7)
    ASSIGNMENT="## Run 7 of 7: PM Full-Subject Analysis, Fluency/ORF for Grades 3-8, & Cross-Year Validation

Three blind spots remain: (1) Performance Matters has ELA, Math, Science, and Social Studies data but only PM Science was correlated with LEAP in Run 6. (2) The fluency dataset (ORF/DIBELS/Amplify/AIMSWeb) was never analyzed for grades 3-8. (3) All correlations are based on a single year — we have never validated whether they hold across years.

### Part A: Performance Matters — All Subjects vs LEAP

1. **PM Subject inventory**: Query \`fls-data-warehouse.performance_matters.results_raw_2024_2025\` to get DISTINCT Subject values with COUNT of rows and COUNT(DISTINCT State_StudentNumber). Confirm ELA, Math, Science, Social Studies exist. Also query DISTINCT Assessment_Category per Subject to understand test types.

2. **PM ELA → LEAP ELA**: Aggregate PM ELA results per student: for each student (State_StudentNumber), compute Overall_Test_Score average or SUM(LA_State_Standard_Points_Earned)/SUM(LA_State_Standard_Points_Possible) across all ELA tests. Join to LEAP 24_25 on LASID (SAFE_CAST State_StudentNumber to match). Compute Pearson r with LEAP ELAScaleScore. **Break down by Assessment_Category** — are Standards Checkpoints, Tests, End of Module, or Reading Checkpoints individually as predictive as anet ELA (r=0.633)?

3. **PM Math → LEAP Math**: Same approach. Aggregate PM Math per student. Correlate with LEAP MathScaleScore. Break down by Assessment_Category. Compare to anet Math (r=0.687-0.694). Are PM Math Tests or Standards Checkpoints competitive?

4. **PM Science → LEAP Science** (extend Run 6): Run 6 found r=0.641 overall. Now break down by Assessment_Category: Standards Checkpoints (n=1,628) vs Tests (n=1,834) vs End of Module (n=80). Which PM Science test type is the strongest predictor? Run 6 excluded Quizzes — verify this was correct by also computing the Quiz correlation.

5. **PM Social Studies → LEAP Social Studies**: Run 6 found NO Social Studies data in PM for 2024-25. **Re-verify this** by querying results_raw (not just results_raw_2024_2025) for Subject LIKE '%Social%' or '%SS%' or '%History%' or '%Civics%'. Also check the non-year-specific results_raw table. If PM SS data exists in any form, correlate with LEAP SocialStudiesScaleScore. Note: learnings say DBQ (14 tests), Quiz (104), Standards Checkpoint (30), Test (26) exist for Social Studies from Run 2 pm_summary.txt — investigate the discrepancy with Run 6 finding of 'zero SS data.'

6. **PM vs anet head-to-head**: For students who have BOTH PM and anet scores in the same subject, compare predictive power directly. Are there students covered by PM but NOT by anet (or vice versa)? What is the incremental coverage?

7. **School and grade breakdowns**: For each PM subject → LEAP correlation, break down by school (Ashe, Green, LHA, Wheatley) and grade level. Are certain schools' PM assessments better aligned with LEAP than others?

### Part B: Fluency/ORF/DIBELS for Grades 3-8

8. **Fluency data audit for grades 3-8**: Query \`fls-data-warehouse.fluency.orf_data_combined\` filtering for Grade_Level IN (3,4,5,6,7,8). How many students? Which schools? What is the BOY/MOY/EOY coverage? Key columns: Student_Number, State_StudentNumber, Grade_Level, School_Short_Name, School_Year, BOY_Reading_Fluency_ORF_Score, MOY_Reading_Fluency_ORF_Score, EOY_Reading_Fluency_ORF_Score, BOY/MOY/EOY_Reading_Fluency_ORF_National_Norm_Percentile, Met_EOY_Goal.

9. **DIBELS for grades 3-8**: Query \`fls-data-warehouse.fluency.dibels_data_combined_acl\` for Grade_Level IN (3,4,5,6,7,8). Key columns: Student_Number, State_StudentNumber, Grade_Level, School_Year_Name, Benchmark_Period, Composite_Score, Composite_National_Norm_Percentile, Composite_Level, Reading_Fluency_ORF_Score, Reading_Fluency_ORF_National_Norm_Percentile, Reading_Comprehension_Maze_Score, Reading_Accuracy_ORF_Accu_Score. How many students per grade?

10. **Amplify benchmark data for grades 3-8**: Query \`fls-data-warehouse.fluency.amplify_benchmark_results\` for Enrollment_Grade IN ('3','4','5','6','7','8') — note Enrollment_Grade is STRING. Key scores: Composite_Score, Reading_Fluency_ORF_Score, Reading_Comprehension_Maze_Score, Reading_Accuracy_ORF_Accu_Score. Also check AIMSWeb: \`fls-data-warehouse.fluency.aimsweb_bm_pm_results\` for StudentGrade IN ('3','4','5','6','7','8').

11. **ORF → LEAP ELA correlation**: For students with both ORF scores (from any fluency table) and LEAP ELA results, compute Pearson r. Join on State_StudentNumber = LASID (SAFE_CAST as needed). Test BOY, MOY, and EOY ORF scores separately. **Is ORF as predictive as anet ELA (r=0.633)?** Also correlate ORF with LEAP Science and Social Studies (reading fluency may predict content area performance).

12. **DIBELS Composite → LEAP**: Correlate DIBELS Composite_Score and Composite_National_Norm_Percentile with all four LEAP subjects. How does it compare to ORF alone?

13. **Maze (reading comprehension) → LEAP**: Correlate Reading_Comprehension_Maze_Score with LEAP ELA and Science. Maze measures comprehension, not just fluency — it may predict differently.

14. **ORF benchmark status as screening tool**: For students flagged as Below Benchmark on ORF (Composite_Level or Reading_Fluency_ORF_Level), what is their LEAP proficiency rate? Build a concordance table similar to Run 4: ORF Below Benchmark + LEAP Below Basic = true negative, ORF At/Above Benchmark + LEAP Below Basic = false positive, etc.

15. **School and grade breakdowns**: Break down all fluency → LEAP correlations by school and grade.

### Part C: Cross-Year Validation

16. **How far back does each system go?** For each assessment system, query the earliest and latest data available:
    - LEAP: Query each school's earliest table (e.g., \`399001LEAPData17_18\`) — SELECT COUNT(*), MIN(CAST(Grade AS INT64)), MAX(CAST(Grade AS INT64)) to confirm coverage. Do this for 17_18, 18_19, 20_21, 21_22, 22_23, 23_24. Note: 19_20 is missing (COVID cancellation).
    - anet: Tables exist for 23_24, 24_25, 25_26. Query row counts for each.
    - PM: Check if results_raw has School_Year values before 2025. Query SELECT DISTINCT School_Year, COUNT(*) FROM results_raw GROUP BY 1.
    - Fluency: Query SELECT DISTINCT School_Year FROM orf_data_combined. Also check amplify_benchmark_results for School_Year values.
    - easyCBM: \`fls-data-warehouse.easycbm.25_26_boy\` and \`25_26_moy\` — confirm only 25-26 exists.

17. **Cross-year replication: 23-24 anet → 22-23 LEAP**: anet 23_24 BOY data exists (ela_boy_23_24, math_boy_23_24). LEAP 22_23 exists (399001LEAPData22_23, etc.). Join on LASID/sas_id. Compute the same correlations as Run 4: anet ELA BOY → LEAP ELA, anet Math BOY → LEAP Math. **Do the r values from the primary analysis (r=0.633 ELA, r=0.687 Math) replicate?**

18. **Cross-year replication: 24-25 anet → 23-24 LEAP**: This was the primary analysis year from Runs 4-5. Verify the exact r values match what was reported. This serves as a sanity check.

19. **LEAP trend stability**: Using the 7 years of LEAP data (17_18 through 24_25, minus 19_20), compute year-over-year correlation of school-level proficiency rates. Are school rankings stable? Is a school that was strong in 17_18 still strong in 24_25?

20. **PM historical depth**: If results_raw contains data before 2024-25, correlate PM scores from the earlier year with LEAP from the corresponding year. Does PM prediction hold across years?

### Output:
- Create a self-contained HTML artifact at \`$OUTPUT_DIR/pm-fluency-validation.html\` with:
  - PM all-subjects correlation table with Assessment_Category breakdowns (head-to-head vs anet)
  - Fluency/ORF grade 3-8 coverage summary and LEAP correlation results
  - ORF concordance table (benchmark status vs LEAP proficiency)
  - Cross-year validation results: do correlations replicate?
  - Historical data depth timeline graphic
  - School-level and grade-level breakdowns throughout
- Append ALL findings to the learnings file under '## Run 7 - PM Full-Subject, Fluency/ORF, & Cross-Year Validation'"
    ;;
8)
    ASSIGNMENT="## Run 8 of 8: Multivariate Prediction Model & Operationalization

Runs 1-7 established the predictive power of individual assessment systems. PM emerged as the strongest single predictor (r=0.71-0.83), anet BOY as the best early-warning signal (r=0.63-0.69 in September), and MAP Math as the highest single-r predictor (r=0.840 but 26% coverage). This run builds the actual multivariate prediction model and produces operationalizable outputs.

### Part A: Data Extract — Build the Master Student Dataset

1. **Extract the master prediction dataset**: Build a single flat file with one row per student who has LEAP 2023-2024 data. For each student, pull:
   - **LEAP outcomes (dependent variables)**: ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialStudiesScaleScore, ELAAchievement, MathAchievement, ScienceAchievement, SocialStudiesAchievement from the 24_25 LEAP tables (399001-399005). CAST scale scores to FLOAT64.
   - **anet BOY (September predictors)**: From ela_boy_24_25 and math_boy_24_25, compute per-student percent correct: SUM(points_received)/SUM(points_possible). Join on sas_id = LASID.
   - **anet MOY (January predictors)**: Same from ela_moy_24_25 and math_moy_24_25.
   - **anet EOY (Spring predictors)**: Same from ela_eoy_24_25 and math_eoy_24_25 if available.
   - **PM aggregate scores**: From \`performance_matters.results_raw_2024_2025\`, compute per-student average Overall_Test_Score for each Subject (English, Math, Science, 'Social Stu'). Join on State_StudentNumber = LASID. Also compute per-student scores broken out by Assessment_Category (Quiz, Test, Standards Checkpoint, etc.).
   - **MAP scores**: From \`map.24_25_boy\` and \`map.24_25_moy\`, pull TestRITScore and TestPercentile by Subject. Join on LASID.
   - **ORF scores**: From \`fluency.orf_data_combined\` for School_Year=2024 and Grade_Level IN (3,4,5,6,7,8), pull BOY_Reading_Fluency_ORF_Score, MOY_Reading_Fluency_ORF_Score. Join on State_StudentNumber = LASID.
   - **Course grades**: From \`grades.current_grades_2024_2025\`, compute average grade percentage for ELA and Math courses. Join on Student_Number or LASID.
   - **Demographics**: School, Grade, from LEAP or roster table.
   Save the extract as a JSON file in the output directory. Report the n and coverage rate for each predictor column.

2. **Handle missing data**: Report the missingness pattern. How many students have all predictors? How many are missing MAP (expected: ~74%)? How many are missing ORF? Build a coverage matrix showing which predictor combinations are available for how many students.

### Part B: Multivariate Regression Models

3. **ELA prediction model**: Using Python (scipy, numpy, or sklearn if available — check with \`pip list\` first), fit multiple linear regression models predicting LEAP ELA Scale Score:
   - Model 1: anet ELA BOY only (baseline — September signal)
   - Model 2: PM ELA only (strongest single predictor)
   - Model 3: anet ELA BOY + PM ELA (does combining help?)
   - Model 4: anet ELA BOY + PM ELA + ORF BOY (does fluency add anything?)
   - Model 5: anet ELA BOY + PM ELA + ORF BOY + Course grade ELA (kitchen sink)
   - Model 6: PM ELA + PM Science + PM Social Studies (cross-subject PM)
   For each model report: R-squared, adjusted R-squared, coefficient for each predictor with p-value, and the incremental R-squared gain from adding each predictor. Use listwise deletion for missing data (analyze only students with all predictors in that model).

4. **Math prediction model**: Same approach predicting LEAP Math Scale Score:
   - Model 1: anet Math BOY only
   - Model 2: PM Math only
   - Model 3: anet Math BOY + PM Math
   - Model 4: anet Math BOY + PM Math + MAP Math BOY %ile (for the ~26% with MAP)
   - Model 5: anet Math BOY + PM Math + Course grade Math
   - Model 6: PM Math + PM Science (cross-subject)

5. **Science prediction model**: Predicting LEAP Science Scale Score:
   - Model 1: PM Science only (r=0.714, best single predictor)
   - Model 2: anet ELA BOY + PM Science (reading → science pathway)
   - Model 3: PM Science + PM ELA + PM Math (all PM subjects)
   - Model 4: PM Science + anet ELA BOY + ORF BOY (all available reading signals)

6. **Social Studies prediction model**: Predicting LEAP Social Studies Scale Score:
   - Model 1: PM Social Studies only (r=0.741)
   - Model 2: anet ELA BOY + PM Social Studies
   - Model 3: PM Social Studies + PM ELA + PM Science (all PM subjects)

7. **Train/test validation**: For the best model per subject, do a proper 70/30 train/test split. Train on 70%, predict on the held-out 30%. Report the test-set R-squared, RMSE, and MAE. Compare test-set performance to training-set performance to check for overfitting. Repeat with 5 random splits and report mean ± SD of test R-squared.

### Part C: Operationalizable Risk Tiers

8. **Calibrate risk tiers from the best model**: Using the best model per subject, compute predicted LEAP scale scores for all students. Map predicted scores to LEAP achievement levels using the known cut scores:
   - Unsatisfactory: below ~725 (verify exact cuts from data)
   - Approaching Basic: ~725-749
   - Basic: ~750-774
   - Mastery: ~775-799
   - Advanced: 800+
   Define risk tiers based on predicted achievement:
   - **On Track**: predicted Mastery or Advanced
   - **Watch**: predicted Basic (could go either way)
   - **Intervention**: predicted Approaching Basic
   - **Crisis**: predicted Unsatisfactory
   Report: n in each tier, actual LEAP proficiency rate per tier, sensitivity (% of actual Unsatisfactory caught by Crisis+Intervention tiers), specificity, false positive rate.

9. **Compare model-based tiers to Run 5 simple tiers**: Run 5 created risk tiers from anet BOY alone. How do the multivariate model tiers compare? Do they catch more at-risk students? Fewer false alarms?

10. **School-specific model performance**: Does the model perform equally well at all 4 schools? Report R-squared and tier accuracy by school. If one school has systematically worse prediction, investigate why.

11. **Grade-specific model performance**: Report R-squared by grade level. Are certain grades harder to predict?

### Part D: Prediction Equations for Operationalization

12. **Write out the final prediction equations**: For each subject, express the best model as a simple formula that could be implemented in a spreadsheet or dashboard:
    - LEAP_ELA_predicted = b0 + b1*(anet_ELA_BOY) + b2*(PM_ELA_avg) + ...
    - Include the actual coefficient values, intercept, and R-squared
    - Include the risk tier cut points

13. **September vs Mid-Year comparison**: What is the R-squared if you can only use September data (anet BOY, MAP BOY, ORF BOY) vs mid-year data (adding PM, MOY scores)? Quantify exactly how much prediction improves from September to January/February.

14. **Identify the diminishing returns boundary**: At what point does adding another predictor gain less than 0.01 R-squared? Document the point of diminishing returns for each subject.

### Output:
- Create a self-contained HTML artifact at \`$OUTPUT_DIR/prediction-model.html\` with:
  - Model comparison tables for each subject (R-squared, coefficients, p-values)
  - Train/test validation results
  - Risk tier distribution and accuracy tables
  - Prediction equations in copy-pasteable format
  - September vs mid-year comparison chart
  - School-level and grade-level model performance
  - Diminishing returns analysis
- Append ALL findings to the learnings file under '## Run 8 - Multivariate Prediction Model'"
    ;;
9)
    ASSIGNMENT="## Run 9 of 9: PM Standards-Level Diagnostic Analysis

Run 8 established that PM is the strongest LEAP predictor (r=0.71-0.83 across all 4 subjects). But the aggregate PM score tells a teacher 'this student is at risk' without telling them WHERE to focus instruction. This run drills into the 1,036,303 rows of PM standard-level data (\`LA_State_Standard\` with \`LA_State_Standard_Points_Earned\` / \`LA_State_Standard_Points_Possible\`) to build a diagnostic map: which specific standards predict which LEAP outcomes, and which standards are instructional dead weight?

### Part A: PM Standards Taxonomy

1. **Full standards inventory**: Query \`fls-data-warehouse.performance_matters.results_raw_2024_2025\` for:
   \`\`\`sql
   SELECT Subject, LA_State_Standard, COUNT(*) as rows,
          COUNT(DISTINCT State_StudentNumber) as students,
          AVG(SAFE_DIVIDE(LA_State_Standard_Points_Earned, LA_State_Standard_Points_Possible)) as avg_pct_correct
   FROM \\\`fls-data-warehouse.performance_matters.results_raw_2024_2025\\\`
   WHERE LA_State_Standard IS NOT NULL AND LA_State_Standard != ''
   GROUP BY 1, 2
   ORDER BY 1, 4 DESC
   \`\`\`
   Report the full taxonomy: how many distinct standards per subject? What are they named? How many students per standard? What is the mean percent correct? IMPORTANT: The Subject value for Social Studies is 'Social Stu' (truncated — discovered in Run 7).

2. **Standards by Assessment_Category**: For each standard, which Assessment_Categories test it? Are certain standards only tested by Quizzes while others appear on Standards Checkpoints and Tests? This matters because Run 7 showed Quizzes had the highest aggregate correlation.
   \`\`\`sql
   SELECT Subject, LA_State_Standard, Assessment_Category,
          COUNT(DISTINCT State_StudentNumber) as students,
          AVG(SAFE_DIVIDE(LA_State_Standard_Points_Earned, LA_State_Standard_Points_Possible)) as avg_pct
   FROM \\\`fls-data-warehouse.performance_matters.results_raw_2024_2025\\\`
   WHERE LA_State_Standard IS NOT NULL AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
   GROUP BY 1, 2, 3
   ORDER BY 1, 2, 3
   \`\`\`

3. **Standards by school and grade**: Do all schools test the same standards? Are there standards tested at some schools but not others? Query by Subject, LA_State_Standard, School, Grade_Level to find gaps.

### Part B: PM Standards → LEAP Scale Score Correlations

4. **Aggregate PM scores by standard per student**: For each student, compute per-standard proficiency:
   \`\`\`sql
   SELECT State_StudentNumber, Subject, LA_State_Standard,
          SUM(LA_State_Standard_Points_Earned) as pts_earned,
          SUM(LA_State_Standard_Points_Possible) as pts_possible,
          SAFE_DIVIDE(SUM(LA_State_Standard_Points_Earned), SUM(LA_State_Standard_Points_Possible)) as pct_correct
   FROM \\\`fls-data-warehouse.performance_matters.results_raw_2024_2025\\\`
   WHERE LA_State_Standard IS NOT NULL AND LA_State_Standard != ''
     AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
   GROUP BY 1, 2, 3
   \`\`\`
   Save this extract — it will be the basis for all correlation analysis. Join to LEAP 24_25 on State_StudentNumber = LASID (SAFE_CAST as needed).

5. **PM Math standards → LEAP Math**: For each Math standard, compute Pearson r with LEAP MathScaleScore. Rank from highest to lowest. Which Math standards are the strongest LEAP predictors? Which are weakest? Minimum n=100 for inclusion. Report r, R², and n for each standard.

6. **PM ELA standards → LEAP ELA**: Same for English standards → LEAP ELAScaleScore. Are PM Reading standards stronger predictors than PM Writing standards (consistent with Run 6 finding that Reading > Writing for LEAP prediction)?

7. **PM Science standards → LEAP Science**: Same for Science. Are there specific Science standards (e.g., 'Life Science', 'Physical Science', 'Earth Science') that predict LEAP Science better than others?

8. **PM Social Studies standards → LEAP Social Studies**: Same for Social Studies. Run 8 found that PM Science had a LARGER coefficient than PM Social Studies in the LEAP SS prediction model. Do specific SS standards (History, Geography, Civics, Economics) show different predictive patterns? Cross-correlate PM SS standards with LEAP Science too.

### Part C: PM Standards → LEAP Reporting Category Subscores

9. **LEAP subscore reminder**: The LEAP _full tables (399001LEAPData24_25_full, 399002, 399004 — NOT 399005) have reporting category subscores as STRING values ('Weak', 'Moderate', 'Strong'). Convert to ordinal (1=Weak, 2=Moderate, 3=Strong) for correlation. Key ELA subscores: ReadingInformationalText, ReadingLiteraryText, ReadingVocabulary, WrittenExpression, WrittenKnowledge. Key Science subscores: Investigate, Evaluate, ReasonScientifically. Key SS subscores: History, Geography, Civics, Economics. Key Math subscores vary by grade.

10. **Build the PM standard × LEAP subscore heatmap**: For each PM standard (rows), correlate with each LEAP reporting category subscore (columns). This is the diagnostic map. Use ordinal LEAP subscores (1-3). Focus on within-subject first (PM Math standards × LEAP Math subscores), then cross-subject (PM ELA standards × LEAP Science subscores).

11. **Validate Run 6 anet findings with PM data**: Run 6 found 'Reading Informational Text' was the most broadly predictive anet domain. PM likely has a corresponding standard. Does the PM version confirm the finding? Is the PM standard-level correlation stronger than anet's domain-level correlation (expected: yes, because PM has more data points per student)?

### Part D: Actionable Diagnostics

12. **Top 10 / Bottom 10 standards per subject**: Rank all standards by predictive power (r with LEAP scale score). For each subject, identify:
    - **Top 10 highest-impact standards**: These are where instructional investment pays off most. If a student is weak here, they're almost certainly weak on LEAP.
    - **Bottom 10 lowest-impact standards**: These are the standards that DON'T predict LEAP. Instructional time spent here has minimal LEAP payoff. This is potentially the most actionable finding — it tells schools where they may be wasting instructional time.

13. **Standards difficulty vs predictive power**: Plot (or tabulate) each standard's average percent correct against its LEAP correlation. The ideal instructional targets are standards that are HARD (low % correct) AND PREDICTIVE (high r): improving performance on these would yield the largest LEAP gains. Standards that are easy (high % correct) and predictive represent maintained strengths. Standards that are hard but NOT predictive are low-priority.

14. **School-level standard performance gaps**: For the top 10 most predictive standards per subject, compare average percent correct across schools. Are there schools that are particularly weak on high-impact standards? This identifies school-specific instructional priorities.

15. **Grade-level standard coverage**: Which standards are tested at which grade levels? Are there predictive standards that are only tested at certain grades? Build a grade × standard coverage matrix.

16. **Student-level diagnostic profiles**: For the top 5 most predictive standards per subject, compute the number of students who are below 50% on each. How many students are weak on multiple high-impact standards simultaneously? This estimates the size of the intervention population at the standard level.

### Part E: Cross-Subject Standard Prediction (Run 6 Extension)

17. **PM ELA standards → LEAP Science**: Which specific PM ELA standards predict LEAP Science? Run 6 showed 'Reading Informational Text' was the most broadly predictive anet domain. Test whether PM ELA reading standards predict LEAP Science better than PM ELA writing standards.

18. **PM Math standards → LEAP Science**: Which Math standards predict Science? Number sense? Measurement? Data analysis?

19. **PM Science standards → LEAP Social Studies** (and vice versa): Run 8 found PM Science had a larger coefficient than PM Social Studies in the LEAP SS model. Which specific Science standards drive this cross-subject prediction?

### Output:
- Create a self-contained HTML artifact at \`$OUTPUT_DIR/standards-diagnostic.html\` with:
  - Full PM standards taxonomy table (all subjects, standards, n, avg % correct)
  - PM standard → LEAP scale score correlation rankings (top 10 / bottom 10 per subject)
  - PM standard × LEAP subscore heatmap (the diagnostic map)
  - Difficulty vs predictive power scatter/table (instructional targeting quadrants)
  - School-level gaps on high-impact standards
  - Cross-subject standard prediction results
  - Student-level diagnostic profile (how many students weak on multiple high-impact standards)
- Append ALL findings to the learnings file under '## Run 9 - PM Standards-Level Diagnostic Analysis'"
    ;;
*)
    echo "ERROR: Run number must be 1-9. Got: $RUN_NUM"
    exit 1
    ;;
esac

# Compose the full prompt
FULL_PROMPT="$ANALYST

---

DATA DICTIONARY (Join Keys & Gotchas):
$DICT_HEADER

---

CUMULATIVE LEARNINGS FROM PRIOR RUNS:
$PRIOR

---

TODAY'S DATE: $TODAY

OUTPUT DIRECTORY: $OUTPUT_DIR
LEARNINGS FILE (append only): $LEARNINGS
DATA DICTIONARY (full reference): $DATA_DICT

$ASSIGNMENT"

echo ""
echo "Launching Claude CLI for Run $RUN_NUM..."

# Write prompt to file to avoid ARG_MAX shell limit (prompt grows with each run)
PROMPT_FILE="$OUTPUT_DIR/.prompt.txt"
printf '%s' "$FULL_PROMPT" > "$PROMPT_FILE"
echo "Prompt size: $(wc -c < "$PROMPT_FILE") bytes"
echo ""

# Launch Claude -- pipe prompt via stdin to bypass argument length limits
env -u CLAUDECODE claude --model claude-opus-4-6 \
    --dangerously-skip-permissions \
    --output-format text \
    < "$PROMPT_FILE" \
    > "$OUTPUT_DIR/claude-output.log" 2>&1

echo ""
echo "============================================"
echo "Run $RUN_NUM complete."
echo "Output: $OUTPUT_DIR"
echo "Log: $OUTPUT_DIR/claude-output.log"
echo "Learnings: $LEARNINGS"
echo "============================================"
