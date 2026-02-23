SELECT
  TRIM(CAST(State_StudentNumber AS STRING)) AS LASID,
  MAX(SAFE_CAST(BOY_Reading_Fluency_ORF_Score AS FLOAT64)) AS orf_boy,
  MAX(SAFE_CAST(MOY_Reading_Fluency_ORF_Score AS FLOAT64)) AS orf_moy,
  MAX(SAFE_CAST(EOY_Reading_Fluency_ORF_Score AS FLOAT64)) AS orf_eoy
FROM `fls-data-warehouse.fluency.orf_data_combined`
WHERE School_Year = 2024
  AND State_StudentNumber IS NOT NULL
  AND TRIM(CAST(State_StudentNumber AS STRING)) != ""
  AND SAFE_CAST(Grade_Level AS INT64) BETWEEN 3 AND 8
GROUP BY LASID
