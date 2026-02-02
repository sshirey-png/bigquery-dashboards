"""
Simple BigQuery Dashboard Updater for SR2/PMAP2 Tracking
Specifically designed for staff_with_observations_by_type table structure
"""

import json
import re
from google.cloud import bigquery

def get_sr2_pmap2_data():
    """Query SR2 and PMAP2 completion data from BigQuery."""

    # Initialize BigQuery client
    client = bigquery.Client()

    print(f"Connected to project: {client.project}")
    print("\nQuerying SR2/PMAP2 data...")
    print("=" * 60)

    # Query to get completion data by school
    query = """
    SELECT
        Location_Name as school_name,
        COUNT(DISTINCT Email_Address) as total_staff,
        SUM(CASE WHEN self_reflection_2_count >= 1 THEN 1 ELSE 0 END) as sr2_completed,
        SUM(CASE WHEN pmap_2_count >= 1 THEN 1 ELSE 0 END) as pmap2_completed
    FROM `talent-demo-482004.talent_grow_observations.staff_with_observations_by_type`
    WHERE include_in_sr2_pmap2_tracking = TRUE
    GROUP BY Location_Name
    ORDER BY Location_Name
    """

    print("Executing query:")
    print("-" * 60)
    print(query)
    print("-" * 60)

    # Execute query
    query_job = client.query(query)
    results = query_job.result()

    # Process results
    school_data = []

    for row in results:
        school_data.append({
            'name': row['school_name'],
            'sr2Completed': int(row['sr2_completed']),
            'sr2Total': int(row['total_staff']),
            'pmap2Completed': int(row['pmap2_completed']),
            'pmap2Total': int(row['total_staff'])
        })

    print(f"\n✓ Retrieved data for {len(school_data)} schools")

    # Show summary
    if school_data:
        print("\nSummary by school:")
        print("-" * 80)
        print(f"{'School':<40} {'SR2':^15} {'PMAP2':^15}")
        print("-" * 80)

        for school in school_data[:10]:  # Show first 10
            sr2_pct = int((school['sr2Completed'] / school['sr2Total'] * 100) if school['sr2Total'] > 0 else 0)
            pmap2_pct = int((school['pmap2Completed'] / school['pmap2Total'] * 100) if school['pmap2Total'] > 0 else 0)

            print(f"{school['name']:<40} {school['sr2Completed']:>3}/{school['sr2Total']:<3} ({sr2_pct:>3}%)  {school['pmap2Completed']:>3}/{school['pmap2Total']:<3} ({pmap2_pct:>3}%)")

        if len(school_data) > 10:
            print(f"... and {len(school_data) - 10} more schools")

    return school_data

def update_html_file(school_data, html_file='index.html'):
    """Update the index.html file with new school data."""

    print(f"\nUpdating {html_file}...")

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

    print(f"✓ Successfully updated {html_file}!")

def main():
    """Main execution function."""
    print("=" * 60)
    print("SR2 & PMAP2 Dashboard Updater")
    print("=" * 60)
    print()

    try:
        # Get data from BigQuery
        school_data = get_sr2_pmap2_data()

        if not school_data:
            print("\n⚠ No data retrieved. Please check your query and table.")
            return

        # Update HTML file
        update_html_file(school_data)

        print("\n" + "=" * 60)
        print("✓ Dashboard update complete!")
        print("=" * 60)
        print("\nRefresh your browser to see the updated data.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease ensure:")
        print("  1. You've run: gcloud auth application-default login")
        print("  2. You have BigQuery read permissions")
        print("  3. The table exists and has data")

if __name__ == "__main__":
    main()
