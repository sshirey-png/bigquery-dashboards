WITH pm_student AS (
  SELECT
    TRIM(State_StudentNumber) AS LASID,
    CASE
      WHEN Subject = "English" THEN "ELA"
      WHEN Subject = "Math" THEN "Math"
      WHEN Subject = "Science" THEN "Science"
      WHEN Subject LIKE "Social%" THEN "SocStu"
      ELSE Subject
    END AS subj,
    AVG(Overall_Test_Score) AS avg_score
  FROM `fls-data-warehouse.performance_matters.results_raw_2024_2025`
  WHERE State_StudentNumber IS NOT NULL
    AND TRIM(State_StudentNumber) != ""
    AND Overall_Test_Score IS NOT NULL
    AND Assessment_Category IN ("Quiz", "Test", "Standards Checkpoint", "End of Module", "Reading Checkpoint", "Writing Checkpoint", "DBQ")
  GROUP BY LASID, subj
)
SELECT
  LASID,
  MAX(CASE WHEN subj="ELA" THEN avg_score END) AS pm_ela,
  MAX(CASE WHEN subj="Math" THEN avg_score END) AS pm_math,
  MAX(CASE WHEN subj="Science" THEN avg_score END) AS pm_sci,
  MAX(CASE WHEN subj="SocStu" THEN avg_score END) AS pm_ss
FROM pm_student
GROUP BY LASID
