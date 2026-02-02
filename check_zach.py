from google.cloud import bigquery
client = bigquery.Client(project='talent-demo-482004')

# First check the schema
table = client.get_table('talent-demo-482004.talent_grow_observations.staff_master_list_with_function')
print("Schema:")
for field in table.schema:
    print(f"  {field.name} ({field.field_type})")
print()

# Search for Zach O'Donnell
query = """
SELECT
  Employee_Number,
  First_Name,
  Last_Name,
  Email_Address,
  Last_Hire_Date,
  DATE_DIFF(CURRENT_DATE(), DATE(Last_Hire_Date), DAY) / 365.25 as years_of_service,
  Job_Title,
  Function,
  Dept,
  Location_Name,
  Supervisor_Name__Unsecured_,
  Employment_Status
FROM `talent-demo-482004.talent_grow_observations.staff_master_list_with_function`
WHERE LOWER(Email_Address) LIKE '%zodonnell%'
   OR LOWER(Email_Address) LIKE '%zach%'
   OR (LOWER(First_Name) LIKE '%zach%' AND LOWER(Last_Name) LIKE '%donnell%')
"""
results = client.query(query).result()
found = False
for row in results:
    found = True
    print("\n" + "="*60)
    for k, v in dict(row).items():
        print(f'{k}: {v}')

if not found:
    print("No employee found matching Zach O'Donnell")
