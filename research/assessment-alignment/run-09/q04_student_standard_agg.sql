-- Part B: Student-level standard aggregates joined to LEAP
-- This query builds per-student, per-standard proficiency and joins to LEAP scores
WITH leap AS (
  SELECT TRIM(LASID) as LASID,
    SAFE_CAST(ELAScaleScore AS FLOAT64) as ela_ss,
    SAFE_CAST(MathScaleScore AS FLOAT64) as math_ss,
    SAFE_CAST(ScienceScaleScore AS FLOAT64) as sci_ss,
    SAFE_CAST(SocialScaleScore AS FLOAT64) as ss_ss,
    TRIM(ELAAchievement) as ela_ach,
    TRIM(MathAchievement) as math_ach,
    SAFE_CAST(Grade AS INT64) as grade
  FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY TRIM(LASID) ORDER BY LASID) as rn
    FROM (
      SELECT LASID, Grade, ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialScaleScore,
             ELAAchievement, MathAchievement
      FROM `fls-data-warehouse.leap.399001LEAPData24_25`
      UNION ALL
      SELECT LASID, Grade, ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialScaleScore,
             ELAAchievement, MathAchievement
      FROM `fls-data-warehouse.leap.399002LEAPData24_25`
      UNION ALL
      SELECT LASID, Grade, ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialScaleScore,
             ELAAchievement, MathAchievement
      FROM `fls-data-warehouse.leap.399004LEAPData24_25`
      UNION ALL
      SELECT LASID, Grade, ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialScaleScore,
             ELAAchievement, MathAchievement
      FROM `fls-data-warehouse.leap.399005LEAPData24_25`
    )
  )
  WHERE rn = 1
),
pm_student_standard AS (
  SELECT
    State_StudentNumber,
    Subject,
    LA_State_Standard,
    School,
    Grade_Level,
    SUM(SAFE_CAST(LA_State_Standard_Points_Earned AS FLOAT64)) as pts_earned,
    SUM(SAFE_CAST(LA_State_Standard_Points_Possible AS FLOAT64)) as pts_possible,
    SAFE_DIVIDE(
      SUM(SAFE_CAST(LA_State_Standard_Points_Earned AS FLOAT64)),
      SUM(SAFE_CAST(LA_State_Standard_Points_Possible AS FLOAT64))
    ) as pct_correct
  FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
  WHERE LA_State_Standard IS NOT NULL AND LA_State_Standard != ''
    AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
  GROUP BY 1, 2, 3, 4, 5
)
SELECT
  pm.Subject,
  pm.LA_State_Standard,
  COUNT(*) as n,
  AVG(pm.pct_correct) as avg_pct_correct,
  CORR(pm.pct_correct, l.ela_ss) as r_ela,
  CORR(pm.pct_correct, l.math_ss) as r_math,
  CORR(pm.pct_correct, l.sci_ss) as r_sci,
  CORR(pm.pct_correct, l.ss_ss) as r_ss
FROM pm_student_standard pm
INNER JOIN leap l ON pm.State_StudentNumber = l.LASID
GROUP BY 1, 2
HAVING COUNT(*) >= 100
ORDER BY 1, 2
