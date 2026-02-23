WITH leap AS (
  SELECT LASID, ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialScaleScore,
    SAFE_CAST(Grade AS INT64) as grade,
    CASE WHEN TRIM(SchoolName) LIKE '%Ashe%' THEN 'Ashe'
         WHEN TRIM(SchoolName) LIKE '%Green%' THEN 'Green'
         WHEN TRIM(SchoolName) LIKE '%Hughes%' THEN 'LHA'
         WHEN TRIM(SchoolName) LIKE '%Wheatley%' THEN 'Wheatley' END as school,
    ROW_NUMBER() OVER (PARTITION BY LASID ORDER BY ELAScaleScore DESC) as rn
  FROM (
    SELECT * FROM `fls-data-warehouse.leap.399001LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399002LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399004LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399005LEAPData24_25`
  )
),
leap_dedup AS (
  SELECT * FROM leap WHERE rn = 1
),
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
pm_sci AS (
  SELECT State_StudentNumber, AVG(Overall_Test_Score) as pm_score
  FROM (
    SELECT DISTINCT State_StudentNumber, Test_Name, Overall_Test_Score
    FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
    WHERE Subject = 'Science' AND State_StudentNumber IS NOT NULL AND Overall_Test_Score IS NOT NULL
      AND Assessment_Category IS NOT NULL AND Assessment_Category != r'\N'
  )
  GROUP BY State_StudentNumber
),
pm_ss AS (
  SELECT State_StudentNumber, AVG(Overall_Test_Score) as pm_score
  FROM (
    SELECT DISTINCT State_StudentNumber, Test_Name, Overall_Test_Score
    FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
    WHERE Subject = 'Social Stu' AND State_StudentNumber IS NOT NULL AND Overall_Test_Score IS NOT NULL
      AND Assessment_Category IS NOT NULL AND Assessment_Category != r'\N'
  )
  GROUP BY State_StudentNumber
)
SELECT
  'English' as subject,
  CORR(e.pm_score, l.ELAScaleScore) as r,
  COUNT(*) as n,
  AVG(e.pm_score) as pm_mean,
  AVG(l.ELAScaleScore) as leap_mean
FROM pm_ela e INNER JOIN leap_dedup l ON e.State_StudentNumber = l.LASID
UNION ALL
SELECT 'Math', CORR(m.pm_score, l.MathScaleScore), COUNT(*), AVG(m.pm_score), AVG(l.MathScaleScore)
FROM pm_math m INNER JOIN leap_dedup l ON m.State_StudentNumber = l.LASID
UNION ALL
SELECT 'Science', CORR(s.pm_score, l.ScienceScaleScore), COUNT(*), AVG(s.pm_score), AVG(l.ScienceScaleScore)
FROM pm_sci s INNER JOIN leap_dedup l ON s.State_StudentNumber = l.LASID
UNION ALL
SELECT 'Social Studies', CORR(ss.pm_score, l.SocialScaleScore), COUNT(*), AVG(ss.pm_score), AVG(l.SocialScaleScore)
FROM pm_ss ss INNER JOIN leap_dedup l ON ss.State_StudentNumber = l.LASID
