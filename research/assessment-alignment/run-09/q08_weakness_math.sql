WITH pm_student_standard AS (
  SELECT
    State_StudentNumber,
    LA_State_Standard,
    SAFE_DIVIDE(
      SUM(SAFE_CAST(LA_State_Standard_Points_Earned AS FLOAT64)),
      SUM(SAFE_CAST(LA_State_Standard_Points_Possible AS FLOAT64))
    ) as pct_correct
  FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
  WHERE LA_State_Standard IN ('LA.MA.3.OA.A.3', 'LA.MA.8.G.A.3', 'LA.MA.3.OA.B.6', 'LA.MA.3.OA.A.4', 'LA.MA.7.RP.A.2b')
    AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
  GROUP BY 1, 2
)
SELECT
  State_StudentNumber,
  COUNT(*) as standards_tested,
  COUNTIF(pct_correct < 0.5) as weak_count,
  AVG(pct_correct) as avg_pct
FROM pm_student_standard
GROUP BY 1
ORDER BY weak_count DESC
