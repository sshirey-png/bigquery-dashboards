"""
Check the actual schema of the supervisor_dashboard_data view
"""

from google.cloud import bigquery

PROJECT_ID = 'talent-demo-482004'
DATASET_ID = 'talent_grow_observations'
TABLE_ID = 'supervisor_dashboard_data'

client = bigquery.Client(project=PROJECT_ID)

# Get table schema
table = client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")

print("Available columns in supervisor_dashboard_data:")
print("=" * 60)
for field in table.schema:
    print(f"  - {field.name} ({field.field_type})")

print("\n" + "=" * 60)

# Also get a sample row to see what data looks like
query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    LIMIT 1
"""

print("\nSample data (first row):")
print("=" * 60)
query_job = client.query(query)
results = list(query_job.result())

if results:
    row = results[0]
    for key, value in row.items():
        print(f"  {key}: {value}")
else:
    print("  No data found")
