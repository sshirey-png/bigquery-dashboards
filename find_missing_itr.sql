-- Find ITR responses that are NOT showing in the dashboard
-- The dashboard only shows staff who are in the staff master list
-- This query finds emails in the ITR survey that aren't in the dashboard view

WITH itr_responses AS (
  SELECT LOWER(Email_Address) as email
  FROM `talent-demo-482004.intent_to_return.intent_to_return_native`
),
dashboard_staff AS (
  SELECT LOWER(email) as email
  FROM `talent-demo-482004.talent_grow_observations.supervisor_dashboard_data`
)
SELECT i.email as missing_from_dashboard
FROM itr_responses i
LEFT JOIN dashboard_staff d ON i.email = d.email
WHERE d.email IS NULL
ORDER BY i.email
