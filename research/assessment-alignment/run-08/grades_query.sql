WITH roster_bridge AS (
  SELECT DISTINCT
    CAST(Student_Number AS STRING) AS Student_Number,
    CAST(State_StudentNumber AS STRING) AS LASID
  FROM `fls-data-warehouse.student_rosters.student_roster`
  WHERE State_StudentNumber IS NOT NULL
    AND TRIM(CAST(State_StudentNumber AS STRING)) != ""
),
grade_avg AS (
  SELECT
    CAST(g.Student_Number AS STRING) AS Student_Number,
    CASE
      WHEN g.Course_Name LIKE "ELA%" OR g.Course_Name LIKE "English%" THEN "ELA"
      WHEN g.Course_Name LIKE "Math%" OR g.Course_Name = "Algebra I" THEN "Math"
      ELSE NULL
    END AS subj,
    AVG(g.Percent) AS avg_grade
  FROM `fls-data-warehouse.grades.current_grades_2024_2025` g
  WHERE g.Grading_Term = "Y1"
    AND g.Percent IS NOT NULL
    AND (g.Course_Name LIKE "ELA%" OR g.Course_Name LIKE "English%" OR g.Course_Name LIKE "Math%" OR g.Course_Name = "Algebra I")
  GROUP BY Student_Number, subj
)
SELECT
  r.LASID,
  MAX(CASE WHEN ga.subj = "ELA" THEN ga.avg_grade END) AS grade_ela,
  MAX(CASE WHEN ga.subj = "Math" THEN ga.avg_grade END) AS grade_math
FROM grade_avg ga
JOIN roster_bridge r ON ga.Student_Number = r.Student_Number
GROUP BY r.LASID
