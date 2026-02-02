from google.cloud import bigquery
client = bigquery.Client(project='talent-demo-482004')

query = """
SELECT *
FROM `talent-demo-482004.talent_grow_observations.staff_master_list_with_function`
WHERE Last_Name IN ('Winston', 'Adugna')
"""
results = client.query(query).result()
for row in results:
    print(dict(row))

