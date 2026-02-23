-- PM standard-level scores correlated with LEAP universal subscores
WITH leap_full AS (
  SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY TRIM(LASID) ORDER BY LASID) as rn
    FROM (
      SELECT TRIM(LASID) as LASID, SAFE_CAST(Grade AS INT64) as grade,
        CASE ReadingInformationalText WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ela_ri_ord,
        CASE ReadingLiteraryText WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ela_rl_ord,
        CASE ReadingVocabulary WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ela_vocab_ord,
        CASE ELAReadingPerformance WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ela_read_ord,
        CASE ELAWritingPerformance WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ela_write_ord,
        CASE Investigate WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as sci_invest_ord,
        CASE Evaluate WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as sci_eval_ord,
        CASE ReasonScientifically WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as sci_reason_ord,
        CASE MajorContent WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as math_major_ord,
        CASE AdditionalSupportingContent WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as math_addl_ord,
        CASE MathematicalReasoningModeling WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as math_reason_ord,
        CASE EstablishingContext WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ss_context_ord,
        CASE ExaminingSourcesandExpressingClaims WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END as ss_sources_ord
      FROM `fls-data-warehouse.leap.399001LEAPData24_25_full`
      UNION ALL
      SELECT TRIM(LASID), SAFE_CAST(Grade AS INT64),
        CASE ReadingInformationalText WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ReadingLiteraryText WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ReadingVocabulary WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ELAReadingPerformance WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ELAWritingPerformance WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE Investigate WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE Evaluate WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ReasonScientifically WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE MajorContent WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE AdditionalSupportingContent WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE MathematicalReasoningModeling WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE EstablishingContext WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ExaminingSourcesandExpressingClaims WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END
      FROM `fls-data-warehouse.leap.399002LEAPData24_25_full`
      UNION ALL
      SELECT TRIM(LASID), SAFE_CAST(Grade AS INT64),
        CASE ReadingInformationalText WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ReadingLiteraryText WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ReadingVocabulary WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ELAReadingPerformance WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ELAWritingPerformance WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE Investigate WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE Evaluate WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ReasonScientifically WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE MajorContent WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE AdditionalSupportingContent WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE MathematicalReasoningModeling WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE EstablishingContext WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END,
        CASE ExaminingSourcesandExpressingClaims WHEN 'Weak' THEN 1 WHEN 'Moderate' THEN 2 WHEN 'Strong' THEN 3 END
      FROM `fls-data-warehouse.leap.399004LEAPData24_25_full`
    )
  )
  WHERE rn = 1
),
pm_student_standard AS (
  SELECT
    State_StudentNumber,
    Subject,
    LA_State_Standard,
    SAFE_DIVIDE(
      SUM(SAFE_CAST(LA_State_Standard_Points_Earned AS FLOAT64)),
      SUM(SAFE_CAST(LA_State_Standard_Points_Possible AS FLOAT64))
    ) as pct_correct
  FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
  WHERE LA_State_Standard IS NOT NULL AND LA_State_Standard != ''
    AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
  GROUP BY 1, 2, 3
)
SELECT
  pm.Subject,
  pm.LA_State_Standard,
  COUNT(*) as n,
  CORR(pm.pct_correct, l.ela_ri_ord) as r_ela_ri,
  CORR(pm.pct_correct, l.ela_rl_ord) as r_ela_rl,
  CORR(pm.pct_correct, l.ela_vocab_ord) as r_ela_vocab,
  CORR(pm.pct_correct, l.ela_read_ord) as r_ela_read,
  CORR(pm.pct_correct, l.ela_write_ord) as r_ela_write,
  CORR(pm.pct_correct, l.sci_invest_ord) as r_sci_invest,
  CORR(pm.pct_correct, l.sci_eval_ord) as r_sci_eval,
  CORR(pm.pct_correct, l.sci_reason_ord) as r_sci_reason,
  CORR(pm.pct_correct, l.math_major_ord) as r_math_major,
  CORR(pm.pct_correct, l.math_addl_ord) as r_math_addl,
  CORR(pm.pct_correct, l.math_reason_ord) as r_math_reason,
  CORR(pm.pct_correct, l.ss_context_ord) as r_ss_context,
  CORR(pm.pct_correct, l.ss_sources_ord) as r_ss_sources
FROM pm_student_standard pm
INNER JOIN leap_full l ON pm.State_StudentNumber = l.LASID
GROUP BY 1, 2
HAVING COUNT(*) >= 100
ORDER BY 1, 2
