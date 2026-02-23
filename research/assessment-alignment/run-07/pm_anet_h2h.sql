WITH leap AS (
  SELECT LASID, ELAScaleScore, MathScaleScore,
    ROW_NUMBER() OVER (PARTITION BY LASID ORDER BY ELAScaleScore DESC) as rn
  FROM (
    SELECT * FROM `fls-data-warehouse.leap.399001LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399002LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399004LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399005LEAPData24_25`
  )
),
leap_dedup AS (SELECT * FROM leap WHERE rn = 1),
pm_ela AS (
  SELECT State_StudentNumber, AVG(Overall_Test_Score) as pm_score
  FROM (
    SELECT DISTINCT State_StudentNumber, Test_Name, Overall_Test_Score
    FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
    WHERE Subject = 'English' AND State_StudentNumber IS NOT NULL AND Overall_Test_Score IS NOT NULL
      AND Assessment_Category IS NOT NULL AND Assessment_Category != r'\N'
  )
  GROUP BY State_StudentNumber
),
pm_math AS (
  SELECT State_StudentNumber, AVG(Overall_Test_Score) as pm_score
  FROM (
    SELECT DISTINCT State_StudentNumber, Test_Name, Overall_Test_Score
    FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
    WHERE Subject = 'Math' AND State_StudentNumber IS NOT NULL AND Overall_Test_Score IS NOT NULL
      AND Assessment_Category IS NOT NULL AND Assessment_Category != r'\N'
  )
  GROUP BY State_StudentNumber
),
anet_ela AS (
  SELECT sas_id, SUM(points_received)/NULLIF(SUM(points_possible),0)*100 as anet_pct
  FROM (
    SELECT * FROM `fls-data-warehouse.anet.ela_boy_24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.anet.ela_moy_24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.anet.ela_eoy_24_25`
  )
  GROUP BY sas_id
),
anet_math AS (
  SELECT sas_id, SUM(points_received)/NULLIF(SUM(points_possible),0)*100 as anet_pct
  FROM (
    SELECT * FROM `fls-data-warehouse.anet.math_boy_24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.anet.math_moy_24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.anet.math_eoy_24_25`
  )
  GROUP BY sas_id
)
-- Head to head: students who have BOTH PM and anet, vs LEAP
SELECT 'ELA_both' as comparison,
  CORR(pe.pm_score, l.ELAScaleScore) as pm_r,
  CORR(ae.anet_pct, l.ELAScaleScore) as anet_r,
  COUNT(*) as n_both,
  (SELECT COUNT(*) FROM pm_ela pe2 INNER JOIN leap_dedup l2 ON pe2.State_StudentNumber = l2.LASID WHERE pe2.State_StudentNumber NOT IN (SELECT sas_id FROM anet_ela)) as pm_only,
  (SELECT COUNT(*) FROM anet_ela ae2 INNER JOIN leap_dedup l2 ON ae2.sas_id = l2.LASID WHERE ae2.sas_id NOT IN (SELECT State_StudentNumber FROM pm_ela)) as anet_only
FROM pm_ela pe
INNER JOIN anet_ela ae ON pe.State_StudentNumber = ae.sas_id
INNER JOIN leap_dedup l ON pe.State_StudentNumber = l.LASID
UNION ALL
SELECT 'Math_both',
  CORR(pm.pm_score, l.MathScaleScore),
  CORR(am.anet_pct, l.MathScaleScore),
  COUNT(*),
  (SELECT COUNT(*) FROM pm_math pm2 INNER JOIN leap_dedup l2 ON pm2.State_StudentNumber = l2.LASID WHERE pm2.State_StudentNumber NOT IN (SELECT sas_id FROM anet_math)),
  (SELECT COUNT(*) FROM anet_math am2 INNER JOIN leap_dedup l2 ON am2.sas_id = l2.LASID WHERE am2.sas_id NOT IN (SELECT State_StudentNumber FROM pm_math))
FROM pm_math pm
INNER JOIN anet_math am ON pm.State_StudentNumber = am.sas_id
INNER JOIN leap_dedup l ON pm.State_StudentNumber = l.LASID
