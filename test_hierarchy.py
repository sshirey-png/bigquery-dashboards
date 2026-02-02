from google.cloud import bigquery

client = bigquery.Client()

# First, get Emily Hunyadi's supervisor_name format
lookup_query = """
SELECT DISTINCT Supervisor_Name__Unsecured_ AS supervisor_name, Supervisor_Email
FROM `firstline-analytics.supervisor_dashboard.supervisor_dashboard_data`
WHERE LOWER(Supervisor_Email) = LOWER('ehunyadi@firstlineschools.org')
"""
print('=== Emily Hunyadi Supervisor Name Format ===')
results = client.query(lookup_query).result()
emily_supervisor_name = None
for row in results:
    emily_supervisor_name = row.supervisor_name
    print(f'Supervisor Name: {row.supervisor_name}')
    print(f'Email: {row.Supervisor_Email}')

if emily_supervisor_name:
    # Now run the hierarchy query
    hierarchy_query = f"""
    WITH RECURSIVE
    supervisor_lookup AS (
        SELECT DISTINCT
            Supervisor_Name__Unsecured_ AS supervisor_name,
            Supervisor_Email AS supervisor_email
        FROM `firstline-analytics.supervisor_dashboard.supervisor_dashboard_data`
        WHERE Supervisor_Name__Unsecured_ IS NOT NULL
        AND Supervisor_Email IS NOT NULL
    ),
    staff_with_supervisor_format AS (
        SELECT
            s.Email_Address AS employee_email,
            s.Supervisor_Name__Unsecured_ AS reports_to,
            sl.supervisor_name AS employee_supervisor_name
        FROM `firstline-analytics.supervisor_dashboard.staff_master_list` s
        LEFT JOIN supervisor_lookup sl ON LOWER(s.Email_Address) = LOWER(sl.supervisor_email)
        WHERE s.Supervisor_Name__Unsecured_ IS NOT NULL
        AND s.Employment_Status IN ('Active', 'Leave of absence')
    ),
    downline AS (
        SELECT '{emily_supervisor_name}' AS supervisor_name, 0 AS level
        UNION ALL
        SELECT sw.employee_supervisor_name AS supervisor_name, d.level + 1
        FROM staff_with_supervisor_format sw
        INNER JOIN downline d ON sw.reports_to = d.supervisor_name
        WHERE sw.employee_supervisor_name IS NOT NULL
        AND d.level < 10
    )
    SELECT DISTINCT supervisor_name, MIN(level) as level
    FROM downline
    GROUP BY supervisor_name
    ORDER BY level, supervisor_name
    """

    print('')
    print('=== Supervisors Emily Hunyadi Can Access ===')
    results = client.query(hierarchy_query).result()
    for row in results:
        indent = '  ' * row.level
        print(f'{indent}Level {row.level}: {row.supervisor_name}')
else:
    print('Emily Hunyadi not found as a supervisor')
