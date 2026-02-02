"""
BigQuery Dashboard Data Updater
This script queries SR2/PMAP2 data from BigQuery and updates the dashboard HTML file.
"""

import json
import re
from google.cloud import bigquery
from google.oauth2 import service_account
import os

def get_bigquery_client(credentials_path=None, project_id=None):
    """
    Create and return a BigQuery client.

    Args:
        credentials_path: Path to service account JSON file (optional)
        project_id: GCP project ID (optional)

    Returns:
        bigquery.Client object
    """
    if credentials_path and os.path.exists(credentials_path):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/bigquery.readonly"]
        )
        client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    elif project_id:
        client = bigquery.Client(project=project_id)
    else:
        # Use application default credentials
        client = bigquery.Client()

    return client

def list_datasets(client):
    """List all datasets in the project."""
    print(f"\nAvailable datasets in project '{client.project}':")
    print("-" * 50)

    datasets = list(client.list_datasets())

    if datasets:
        for dataset in datasets:
            print(f"  - {dataset.dataset_id}")
        return [dataset.dataset_id for dataset in datasets]
    else:
        print("  No datasets found.")
        return []

def list_tables(client, dataset_id):
    """List all tables in a dataset."""
    print(f"\nAvailable tables in dataset '{dataset_id}':")
    print("-" * 50)

    dataset_ref = client.dataset(dataset_id)
    tables = list(client.list_tables(dataset_ref))

    if tables:
        for table in tables:
            print(f"  - {table.table_id}")
        return [table.table_id for table in tables]
    else:
        print("  No tables found.")
        return []

def get_table_schema(client, dataset_id, table_id):
    """Get and display the schema of a table."""
    print(f"\nSchema for {dataset_id}.{table_id}:")
    print("-" * 50)

    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)

    for field in table.schema:
        print(f"  - {field.name}: {field.field_type}")

    return table.schema

def query_sr2_pmap2_data(client, dataset_id, table_id, school_col, type_col, completed_col, total_col):
    """
    Query SR2 and PMAP2 data from BigQuery.

    Args:
        client: BigQuery client
        dataset_id: Dataset name
        table_id: Table name
        school_col: Column name for school name
        type_col: Column name for type (SR2/PMAP2)
        completed_col: Column name for completed count
        total_col: Column name for total count

    Returns:
        List of school data dictionaries
    """
    query = f"""
    SELECT
        {school_col} as school_name,
        {type_col} as type,
        SUM({completed_col}) as completed,
        SUM({total_col}) as total
    FROM `{client.project}.{dataset_id}.{table_id}`
    WHERE {type_col} IN ('SR2', 'PMAP2')
    GROUP BY {school_col}, {type_col}
    ORDER BY {school_col}, {type_col}
    """

    print("\nExecuting query:")
    print("-" * 50)
    print(query)
    print("-" * 50)

    query_job = client.query(query)
    results = query_job.result()

    # Process results into school data structure
    schools = {}

    for row in results:
        school_name = row['school_name']
        type_name = row['type']
        completed = row['completed']
        total = row['total']

        if school_name not in schools:
            schools[school_name] = {
                'name': school_name,
                'sr2Completed': 0,
                'sr2Total': 0,
                'pmap2Completed': 0,
                'pmap2Total': 0
            }

        if type_name == 'SR2':
            schools[school_name]['sr2Completed'] = completed
            schools[school_name]['sr2Total'] = total
        elif type_name == 'PMAP2':
            schools[school_name]['pmap2Completed'] = completed
            schools[school_name]['pmap2Total'] = total

    return list(schools.values())

def update_html_file(school_data, html_file='index.html'):
    """
    Update the index.html file with new school data.

    Args:
        school_data: List of school data dictionaries
        html_file: Path to the HTML file to update
    """
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Convert school data to JavaScript array format
    js_data = json.dumps(school_data, indent=12)

    # Replace the schoolData array in the HTML file
    pattern = r'const schoolData = \[[\s\S]*?\];'
    replacement = f'const schoolData = {js_data};'

    updated_content = re.sub(pattern, replacement, html_content)

    # Write the updated content back to the file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"\n✓ Successfully updated {html_file} with {len(school_data)} schools!")

def main():
    """Main execution function."""
    print("=" * 60)
    print("BigQuery Dashboard Data Updater")
    print("=" * 60)

    # Step 1: Get BigQuery client
    print("\n[Step 1] Connecting to BigQuery...")

    # You can specify credentials or project here, or use default credentials
    # Option 1: Use service account JSON
    # client = get_bigquery_client(credentials_path='path/to/credentials.json')

    # Option 2: Use project ID with application default credentials
    # client = get_bigquery_client(project_id='your-project-id')

    # Option 3: Use default credentials (will use GOOGLE_APPLICATION_CREDENTIALS env var)
    try:
        client = get_bigquery_client()
        print(f"✓ Connected to project: {client.project}")
    except Exception as e:
        print(f"✗ Error connecting to BigQuery: {e}")
        print("\nPlease ensure you have:")
        print("  1. Installed google-cloud-bigquery: pip install google-cloud-bigquery")
        print("  2. Set up authentication:")
        print("     - Set GOOGLE_APPLICATION_CREDENTIALS environment variable, OR")
        print("     - Run 'gcloud auth application-default login', OR")
        print("     - Provide a service account JSON file")
        return

    # Step 2: List datasets
    print("\n[Step 2] Discovering datasets...")
    datasets = list_datasets(client)

    if not datasets:
        print("\n✗ No datasets found. Please check your permissions.")
        return

    # Step 3: Get dataset from user
    print("\n" + "=" * 60)
    dataset_id = input("Enter the dataset name to use: ").strip()

    if dataset_id not in datasets:
        print(f"\n⚠ Warning: '{dataset_id}' not found in the list above.")
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return

    # Step 4: List tables
    print(f"\n[Step 3] Discovering tables in '{dataset_id}'...")
    tables = list_tables(client, dataset_id)

    if not tables:
        print("\n✗ No tables found in this dataset.")
        return

    # Step 5: Get table from user
    print("\n" + "=" * 60)
    table_id = input("Enter the table name to use: ").strip()

    if table_id not in tables:
        print(f"\n⚠ Warning: '{table_id}' not found in the list above.")
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return

    # Step 6: Get table schema
    print(f"\n[Step 4] Examining table schema...")
    schema = get_table_schema(client, dataset_id, table_id)

    # Step 7: Get column mappings from user
    print("\n" + "=" * 60)
    print("Enter the column names for the following fields:")
    print("-" * 60)
    school_col = input("School name column: ").strip()
    type_col = input("Type column (SR2/PMAP2 indicator): ").strip()
    completed_col = input("Completed count column: ").strip()
    total_col = input("Total count column: ").strip()

    # Step 8: Query data
    print(f"\n[Step 5] Querying SR2/PMAP2 data...")
    try:
        school_data = query_sr2_pmap2_data(
            client, dataset_id, table_id,
            school_col, type_col, completed_col, total_col
        )

        print(f"\n✓ Retrieved data for {len(school_data)} schools")

        # Display sample data
        if school_data:
            print("\nSample data (first 3 schools):")
            print("-" * 60)
            for school in school_data[:3]:
                print(f"  {school['name']}")
                print(f"    SR2: {school['sr2Completed']}/{school['sr2Total']}")
                print(f"    PMAP2: {school['pmap2Completed']}/{school['pmap2Total']}")

    except Exception as e:
        print(f"\n✗ Error querying data: {e}")
        return

    # Step 9: Update HTML file
    print(f"\n[Step 6] Updating dashboard...")
    try:
        update_html_file(school_data)
        print("\n" + "=" * 60)
        print("✓ Dashboard update complete!")
        print("=" * 60)
        print("\nYou can now refresh your browser to see the updated data.")
    except Exception as e:
        print(f"\n✗ Error updating HTML file: {e}")
        return

if __name__ == "__main__":
    main()
