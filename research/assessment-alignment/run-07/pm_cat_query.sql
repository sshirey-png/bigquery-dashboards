WITH leap AS (
  SELECT LASID, ELAScaleScore, MathScaleScore, ScienceScaleScore, SocialScaleScore,
    SAFE_CAST(Grade AS INT64) as grade,
    ROW_NUMBER() OVER (PARTITION BY LASID ORDER BY ELAScaleScore DESC) as rn
  FROM (
    SELECT * FROM `fls-data-warehouse.leap.399001LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399002LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399004LEAPData24_25`
    UNION ALL SELECT * FROM `fls-data-warehouse.leap.399005LEAPData24_25`
  )
),
leap_dedup AS (SELECT * FROM leap WHERE rn = 1),
pm_by_cat AS (
  SELECT State_StudentNumber, Subject, Assessment_Category,
    AVG(Overall_Test_Score) as pm_score
  FROM (
    SELECT DISTINCT State_StudentNumber, Subject, Assessment_Category, Test_Name, Overall_Test_Score
    FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
    WHERE State_StudentNumber IS NOT NULL AND Overall_Test_Score IS NOT NULL
      AND Subject IN ('English','Math','Science','Social Stu')
      AND Assessment_Category IS NOT NULL AND Assessment_Category != r'\N'
  )
  GROUP BY State_StudentNumber, Subject, Assessment_Category
)
-- English by category
SELECT p.Subject, p.Assessment_Category,
  CORR(p.pm_score, l.ELAScaleScore) as r, COUNT(*) as n, AVG(p.pm_score) as pm_mean
FROM pm_by_cat p INNER JOIN leap_dedup l ON p.State_StudentNumber = l.LASID
WHERE p.Subject = 'English'
GROUP BY p.Subject, p.Assessment_Category
UNION ALL
-- Math by category
SELECT p.Subject, p.Assessment_Category,
  CORR(p.pm_score, l.MathScaleScore) as r, COUNT(*) as n, AVG(p.pm_score) as pm_mean
FROM pm_by_cat p INNER JOIN leap_dedup l ON p.State_StudentNumber = l.LASID
WHERE p.Subject = 'Math'
GROUP BY p.Subject, p.Assessment_Category
UNION ALL
-- Science by category
SELECT p.Subject, p.Assessment_Category,
  CORR(p.pm_score, l.ScienceScaleScore) as r, COUNT(*) as n, AVG(p.pm_score) as pm_mean
FROM pm_by_cat p INNER JOIN leap_dedup l ON p.State_StudentNumber = l.LASID
WHERE p.Subject = 'Science'
GROUP BY p.Subject, p.Assessment_Category
UNION ALL
-- Social Studies by category
SELECT p.Subject, p.Assessment_Category,
  CORR(p.pm_score, l.SocialScaleScore) as r, COUNT(*) as n, AVG(p.pm_score) as pm_mean
FROM pm_by_cat p INNER JOIN leap_dedup l ON p.State_StudentNumber = l.LASID
WHERE p.Subject = 'Social Stu'
GROUP BY p.Subject, p.Assessment_Category
ORDER BY Subject, r DESC
