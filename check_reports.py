from google.cloud import bigquery
client = bigquery.Client(project='talent-demo-482004')

# Find Charlotte Steele
query0 = """
SELECT First_Name, Last_Name, Job_Title, Supervisor_Name__Unsecured_, Dept
FROM `talent-demo-482004.talent_grow_observations.staff_master_list`
WHERE Last_Name = 'Steele'
AND Employment_Status = 'Active'
"""
results0 = client.query(query0).result()
print('=== Charlotte Steele ===')
for row in results0:
    print(f'{row.First_Name} {row.Last_Name} - {row.Job_Title} - Reports to: {row.Supervisor_Name__Unsecured_} - Dept: {row.Dept}')

# Find Michael Burbano and Zach O'Donnell
query = """
SELECT First_Name, Last_Name, Job_Title, Supervisor_Name__Unsecured_, Dept
FROM `talent-demo-482004.talent_grow_observations.staff_master_list`
WHERE Last_Name IN ('Burbano', "O'Donnell")
AND Employment_Status = 'Active'
"""
results = client.query(query).result()
print('=== Michael and Zach ===')
for row in results:
    print(f'{row.First_Name} {row.Last_Name} - {row.Job_Title} - Reports to: {row.Supervisor_Name__Unsecured_} - Dept: {row.Dept}')

# Find their direct reports
query2 = """
SELECT First_Name, Last_Name, Job_Title, Supervisor_Name__Unsecured_
FROM `talent-demo-482004.talent_grow_observations.staff_master_list`
WHERE (Supervisor_Name__Unsecured_ LIKE '%Burbano%' OR Supervisor_Name__Unsecured_ LIKE "%O'Donnell%")
AND Employment_Status = 'Active'
"""
results2 = client.query(query2).result()
print('\n=== Their Direct Reports ===')
for row in results2:
    print(f'{row.First_Name} {row.Last_Name} - {row.Job_Title} - Reports to: {row.Supervisor_Name__Unsecured_}')
