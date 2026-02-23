WITH map_pivot AS (
  SELECT
    TRIM(Student_StateID) AS LASID,
    CASE WHEN Subject = "Language Arts" THEN "ELA" WHEN Subject = "Mathematics" THEN "Math" ELSE Subject END AS subj,
    CASE WHEN TermName LIKE "Fall%" THEN "BOY" WHEN TermName LIKE "Winter%" THEN "MOY" WHEN TermName LIKE "Spring%" THEN "EOY" END AS term,
    TestRITScore AS rit,
    TestPercentile AS pctile
  FROM `fls-data-warehouse.map.24_25_boy`
  WHERE Student_StateID IS NOT NULL AND TRIM(Student_StateID) != ""
  UNION ALL
  SELECT
    TRIM(Student_StateID),
    CASE WHEN Subject = "Language Arts" THEN "ELA" WHEN Subject = "Mathematics" THEN "Math" ELSE Subject END,
    CASE WHEN TermName LIKE "Fall%" THEN "BOY" WHEN TermName LIKE "Winter%" THEN "MOY" WHEN TermName LIKE "Spring%" THEN "EOY" END,
    TestRITScore, TestPercentile
  FROM `fls-data-warehouse.map.24_25_moy`
  WHERE Student_StateID IS NOT NULL AND TRIM(Student_StateID) != ""
)
SELECT
  LASID,
  MAX(CASE WHEN subj="ELA" AND term="BOY" THEN rit END) AS map_ela_boy_rit,
  MAX(CASE WHEN subj="ELA" AND term="BOY" THEN pctile END) AS map_ela_boy_pctile,
  MAX(CASE WHEN subj="ELA" AND term="MOY" THEN rit END) AS map_ela_moy_rit,
  MAX(CASE WHEN subj="ELA" AND term="MOY" THEN pctile END) AS map_ela_moy_pctile,
  MAX(CASE WHEN subj="Math" AND term="BOY" THEN rit END) AS map_math_boy_rit,
  MAX(CASE WHEN subj="Math" AND term="BOY" THEN pctile END) AS map_math_boy_pctile,
  MAX(CASE WHEN subj="Math" AND term="MOY" THEN rit END) AS map_math_moy_rit,
  MAX(CASE WHEN subj="Math" AND term="MOY" THEN pctile END) AS map_math_moy_pctile
FROM map_pivot
GROUP BY LASID
