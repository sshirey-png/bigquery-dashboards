from google.cloud import bigquery
client = bigquery.Client(project='talent-demo-482004')

# Update the application using parameterized query
query = """
UPDATE `talent-demo-482004.sabbatical.applications`
SET employee_name = @employee_name,
    employee_email = @employee_email,
    updated_at = CURRENT_TIMESTAMP()
WHERE application_id = @application_id
"""

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("employee_name", "STRING", "Zachary O'Donnell"),
        bigquery.ScalarQueryParameter("employee_email", "STRING", "zodonnell@firstlineschools.org"),
        bigquery.ScalarQueryParameter("application_id", "STRING", "2D94CBC8"),
    ]
)

client.query(query, job_config=job_config).result()
print('Updated successfully!')

# Verify the update
verify = """
SELECT application_id, employee_name, employee_email, status
FROM `talent-demo-482004.sabbatical.applications`
WHERE application_id = '2D94CBC8'
"""
results = client.query(verify).result()
for row in results:
    print(f'ID: {row.application_id}')
    print(f'Name: {row.employee_name}')
    print(f'Email: {row.employee_email}')
    print(f'Status: {row.status}')
