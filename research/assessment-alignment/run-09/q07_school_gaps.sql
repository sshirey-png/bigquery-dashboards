WITH pm_student_standard AS (
  SELECT
    State_StudentNumber,
    Subject,
    LA_State_Standard,
    School,
    Grade_Level,
    SAFE_DIVIDE(
      SUM(SAFE_CAST(LA_State_Standard_Points_Earned AS FLOAT64)),
      SUM(SAFE_CAST(LA_State_Standard_Points_Possible AS FLOAT64))
    ) as pct_correct
  FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
  WHERE LA_State_Standard IN ('LA.MA.3.OA.A.3', 'LA.MA.8.G.A.3', 'LA.MA.3.OA.B.6', 'LA.MA.3.OA.A.4', 'LA.MA.7.RP.A.2b', 'LA.MA.3.MD.A.1', 'LA.MA.3.MD.C.7', 'LA.MA.7.RP.A.2a', 'CCSS.Math.Content.4.NBT.A.3', 'LA.MA.3.OA.A.1', 'CCSS.ELA-Literacy.RL.3.1', 'CCSS.ELA-Literacy.W.4.2', 'CCSS.ELA-Literacy.W.4.3', 'CCSS.ELA-Literacy.W.8.2', 'CCSS.ELA-Literacy.W.4.1', 'CCSS.ELA-Literacy.RL.3.3', 'CCSS.ELA-Literacy.RL.7.1', 'CCSS.ELA-Literacy.RL.4.1', 'CCSS.ELA-Literacy.RL.5.1', 'CCSS.ELA-Literacy.W.3.2', 'LA.17.SCI.5-PS1-4', 'LA.17.SCI.3-LS3-2', 'LA.17.SCI.5-PS1-3', 'NGSS.SCI.5-ESS2-2', 'NGSS.SCI.CCC.3-5.3.2', 'LA.17.SCI.5-ESS1-1', 'NGSS.SCI.MS-LS1-3', 'LA.17.SCI.5-LS2-1', 'NGSS.SCI.CCC.3-5.4.0', 'NGSS.SCI.DCI.5-ESS2.A.1', 'LA.22.SS.5.5.11.b', 'LA.22.SS.3.G.3.26', 'LA.22.SS.6.6.11.c', 'LA.22.SS.6.6.9.f', 'LA.22.SS.5.5.11', 'LA.22.SS.4.4.18.c', 'LA.22.SS.5.5.11.c', 'LA.22.SS.7.7.10.g', 'LA.22.SS.8.8.12.c', 'LA.22.SS.3.G.3.28')
    AND Assessment_Category IN ('Quiz','Test','Standards Checkpoint','End of Module','Reading Checkpoint','Writing Checkpoint','DBQ')
  GROUP BY 1, 2, 3, 4, 5
)
SELECT
  Subject,
  LA_State_Standard,
  School,
  COUNT(*) as n,
  AVG(pct_correct) as avg_pct,
  COUNTIF(pct_correct < 0.5) as below_50_count
FROM pm_student_standard
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 20
ORDER BY 1, 2, 3
