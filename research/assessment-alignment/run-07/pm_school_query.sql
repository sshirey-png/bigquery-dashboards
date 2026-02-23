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
leap_dedup AS (SELECT * FROM leap WHERE rn = 1),
pm_all AS (
  SELECT State_StudentNumber, Subject, AVG(Overall_Test_Score) as pm_score
  FROM (
    SELECT DISTINCT State_StudentNumber, Subject, Test_Name, Overall_Test_Score
    FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
    WHERE State_StudentNumber IS NOT NULL AND Overall_Test_Score IS NOT NULL
      AND Subject IN ('English','Math','Science','Social Stu')
      AND Assessment_Category IS NOT NULL AND Assessment_Category != r'\N'
  )
  GROUP BY State_StudentNumber, Subject
)
-- By school
SELECT p.Subject, l.school,
  CASE WHEN p.Subject = 'English' THEN CORR(p.pm_score, l.ELAScaleScore)
       WHEN p.Subject = 'Math' THEN CORR(p.pm_score, l.MathScaleScore)
       WHEN p.Subject = 'Science' THEN CORR(p.pm_score, l.ScienceScaleScore)
       WHEN p.Subject = 'Social Stu' THEN CORR(p.pm_score, l.SocialScaleScore) END as r,
  COUNT(*) as n,
  AVG(p.pm_score) as pm_mean
FROM pm_all p INNER JOIN leap_dedup l ON p.State_StudentNumber = l.LASID
GROUP BY p.Subject, l.school
ORDER BY p.Subject, l.school
