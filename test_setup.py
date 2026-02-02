"""
Quick test script to verify Flask app and BigQuery setup
"""

import sys

print("Testing Supervisor Dashboard Setup...")
print("=" * 60)

# Test 1: Import Flask
print("\n1. Testing Flask import...")
try:
    from flask import Flask
    from flask_cors import CORS
    print("   [OK] Flask and Flask-CORS imported successfully")
except ImportError as e:
    print(f"   [ERROR] Failed to import Flask: {e}")
    sys.exit(1)

# Test 2: Import BigQuery
print("\n2. Testing BigQuery import...")
try:
    from google.cloud import bigquery
    print("   [OK] BigQuery client library imported successfully")
except ImportError as e:
    print(f"   [ERROR] Failed to import BigQuery: {e}")
    sys.exit(1)

# Test 3: Initialize BigQuery client
print("\n3. Testing BigQuery client initialization...")
try:
    client = bigquery.Client(project='talent-demo-482004')
    print("   [OK] BigQuery client initialized successfully")
    print(f"   Project: {client.project}")

    # Test 4: Check view access
    print("\n4. Testing BigQuery view access...")
    try:
        query = """
            SELECT COUNT(*) as count
            FROM `talent-demo-482004.talent_grow_observations.supervisor_dashboard_data`
            LIMIT 1
        """
        query_job = client.query(query)
        results = list(query_job.result())
        print(f"   [OK] Successfully queried view")
        print(f"   Note: Test query executed (checking view exists)")

    except Exception as e:
        print(f"   [ERROR] Failed to query view: {e}")
        print("   This might be expected if the view doesn't exist yet")

except Exception as e:
    print(f"   [WARNING] BigQuery client initialization failed: {e}")
    print("   This is expected if you haven't run: gcloud auth application-default login")

# Test 5: Import the Flask app
print("\n5. Testing Flask app import...")
try:
    import app
    print("   [OK] Flask app module imported successfully")
    print(f"   App name: {app.app.name}")
except Exception as e:
    print(f"   [ERROR] Failed to import app: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Setup test completed!")
print("\nNext steps:")
print("1. If BigQuery authentication failed, run:")
print("   gcloud auth application-default login")
print("2. Ensure the BigQuery view exists:")
print("   talent-demo-482004.talent_grow_observations.supervisor_dashboard_data")
print("3. Start the Flask server:")
print("   py app.py")
print("4. Open browser to: http://localhost:5000")
print("=" * 60)
