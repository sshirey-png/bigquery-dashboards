SELECT
  Subject,
  LA_State_Standard,
  School,
  Grade_Level,
  COUNT(DISTINCT State_StudentNumber) as students,
  AVG(SAFE_DIVIDE(
    SAFE_CAST(LA_State_Standard_Points_Earned AS FLOAT64),
    SAFE_CAST(LA_State_Standard_Points_Possible AS FLOAT64)
  )) as avg_pct
FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
WHERE LA_State_Standard IS NOT NULL AND LA_State_Standard != ''
  AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
