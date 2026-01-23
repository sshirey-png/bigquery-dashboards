#!/usr/bin/env python3
"""
Level Data Grow API to BigQuery Sync Script
Pulls action step assignments from the LDG API and loads them into BigQuery.
Automatically refreshes API token using client credentials.

Usage:
    python ldg_action_steps_sync.py

For daily automation, schedule this script with Task Scheduler (Windows) or cron (Linux).
"""

import requests
import logging
import re
import sys
from datetime import datetime, timezone
from dateutil import parser as date_parser
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Import configuration
try:
    from ldg_config import (
        CLIENT_ID, CLIENT_SECRET, TOKEN_ENDPOINT,
        PROJECT_ID, DATASET_ID, TABLE_ID,
        API_URL, PAGE_SIZE
    )
except ImportError:
    print("ERROR: ldg_config.py not found. Please create it with your credentials.")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# School year filter - only sync records created on or after this date
SCHOOL_YEAR_START = datetime(2025, 7, 1, tzinfo=timezone.utc)

# BigQuery table schema
TABLE_SCHEMA = [
    bigquery.SchemaField("_id", "STRING", mode="REQUIRED", description="Primary key"),
    bigquery.SchemaField("name", "STRING", mode="NULLABLE", description="Action step text (HTML stripped)"),
    bigquery.SchemaField("creator_id", "STRING", mode="NULLABLE", description="Creator user ID"),
    bigquery.SchemaField("creator_name", "STRING", mode="NULLABLE", description="Creator full name"),
    bigquery.SchemaField("creator_email", "STRING", mode="NULLABLE", description="Creator email"),
    bigquery.SchemaField("user_id", "STRING", mode="NULLABLE", description="Teacher user ID"),
    bigquery.SchemaField("user_name", "STRING", mode="NULLABLE", description="Teacher full name"),
    bigquery.SchemaField("user_email", "STRING", mode="NULLABLE", description="Teacher email"),
    bigquery.SchemaField("observation_id", "STRING", mode="NULLABLE", description="Related observation ID"),
    bigquery.SchemaField("progress_percent", "INTEGER", mode="NULLABLE", description="Progress percentage"),
    bigquery.SchemaField("progress_date", "TIMESTAMP", mode="NULLABLE", description="Progress update date"),
    bigquery.SchemaField("tags", "STRING", mode="NULLABLE", description="Comma-separated tag names"),
    bigquery.SchemaField("type", "STRING", mode="NULLABLE", description="Assignment type"),
    bigquery.SchemaField("private", "BOOLEAN", mode="NULLABLE", description="Is private"),
    bigquery.SchemaField("locked", "BOOLEAN", mode="NULLABLE", description="Is locked"),
    bigquery.SchemaField("coachingActivity", "BOOLEAN", mode="NULLABLE", description="Is coaching activity"),
    bigquery.SchemaField("archivedAt", "TIMESTAMP", mode="NULLABLE", description="Archive timestamp"),
    bigquery.SchemaField("created", "TIMESTAMP", mode="NULLABLE", description="Created timestamp"),
    bigquery.SchemaField("lastModified", "TIMESTAMP", mode="NULLABLE", description="Last modified timestamp"),
    bigquery.SchemaField("sync_timestamp", "TIMESTAMP", mode="REQUIRED", description="When this record was synced"),
]


def get_access_token():
    """Get a fresh access token using client credentials."""
    logger.info("Requesting new access token...")

    # Method 1: Basic Auth
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            auth=(CLIENT_ID, CLIENT_SECRET),
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get('token') or data.get('access_token') or data.get('accessToken')
            if token:
                logger.info("Successfully obtained access token via Basic Auth")
                return token
    except Exception as e:
        logger.debug(f"Basic Auth failed: {e}")

    # Method 2: JSON body with different field names
    payloads = [
        {"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
        {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        {"id": CLIENT_ID, "secret": CLIENT_SECRET},
    ]

    for payload in payloads:
        try:
            response = requests.post(
                TOKEN_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('token') or data.get('access_token') or data.get('accessToken')
                if token:
                    logger.info("Successfully obtained access token")
                    return token

            logger.debug(f"Payload {list(payload.keys())} returned {response.status_code}")

        except Exception as e:
            logger.debug(f"Token request failed: {e}")
            continue

    # Log the last response for debugging
    logger.error(f"Token endpoint returned: {response.status_code} - {response.text[:500] if response.text else 'No response'}")
    raise Exception(f"Failed to obtain access token. Status: {response.status_code}")


def strip_html(text):
    """Remove HTML tags from a string."""
    if not text:
        return text
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    clean = clean.replace('&nbsp;', ' ')
    clean = clean.replace('&amp;', '&')
    clean = clean.replace('&lt;', '<')
    clean = clean.replace('&gt;', '>')
    clean = clean.replace('&quot;', '"')
    clean = clean.replace('&#39;', "'")
    # Clean up extra whitespace
    clean = ' '.join(clean.split())
    return clean.strip()


def parse_timestamp(value):
    """Parse ISO timestamp string and return as ISO format string for BigQuery."""
    if not value:
        return None
    try:
        # Handle various ISO formats
        if isinstance(value, str):
            # Remove 'Z' and handle milliseconds
            value = value.replace('Z', '+00:00')
            if '.' in value:
                # Truncate milliseconds to 6 digits if longer
                parts = value.split('.')
                if len(parts) == 2:
                    ms_and_tz = parts[1]
                    if '+' in ms_and_tz:
                        ms, tz = ms_and_tz.split('+')
                        ms = ms[:6]
                        value = f"{parts[0]}.{ms}+{tz}"
                    elif '-' in ms_and_tz and ms_and_tz.index('-') > 0:
                        ms, tz = ms_and_tz.rsplit('-', 1)
                        ms = ms[:6]
                        value = f"{parts[0]}.{ms}-{tz}"
                    else:
                        ms = ms_and_tz[:6]
                        value = f"{parts[0]}.{ms}+00:00"
            # Parse and return as ISO string for JSON serialization
            dt = datetime.fromisoformat(value)
            return dt.isoformat()
        return value
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{value}': {e}")
        return None


def extract_tags(tags_list):
    """Extract tag names as comma-separated string."""
    if not tags_list or not isinstance(tags_list, list):
        return None
    tag_names = []
    for tag in tags_list:
        if isinstance(tag, dict) and 'name' in tag:
            tag_names.append(tag['name'])
        elif isinstance(tag, str):
            tag_names.append(tag)
    return ', '.join(tag_names) if tag_names else None


def is_current_school_year(record):
    """Check if record was created in the current school year."""
    created = record.get('created')
    if not created:
        return False
    try:
        if isinstance(created, str):
            created_dt = date_parser.parse(created)
            # Ensure timezone aware
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            return created_dt >= SCHOOL_YEAR_START
        return False
    except Exception:
        return False


def transform_record(record, sync_time):
    """Transform API record to BigQuery row format."""
    creator = record.get('creator', {}) or {}
    user = record.get('user', {}) or {}
    progress = record.get('progress', {}) or {}

    return {
        '_id': record.get('_id'),
        'name': strip_html(record.get('name')),
        'creator_id': creator.get('_id'),
        'creator_name': creator.get('name'),
        'creator_email': creator.get('email'),
        'user_id': user.get('_id'),
        'user_name': user.get('name'),
        'user_email': user.get('email'),
        'observation_id': record.get('observation'),
        'progress_percent': progress.get('percent'),
        'progress_date': parse_timestamp(progress.get('date')),
        'tags': extract_tags(record.get('tags')),
        'type': record.get('type'),
        'private': record.get('private'),
        'locked': record.get('locked'),
        'coachingActivity': record.get('coachingActivity'),
        'archivedAt': parse_timestamp(record.get('archivedAt')),
        'created': parse_timestamp(record.get('created')),
        'lastModified': parse_timestamp(record.get('lastModified')),
        'sync_timestamp': sync_time,
    }


def fetch_all_records(token):
    """Fetch all records from the API with pagination, filtered to current school year."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    all_records = []
    skip = 0
    total_fetched = 0

    logger.info(f"Starting API data fetch (filtering to records on or after {SCHOOL_YEAR_START.date()})...")

    while True:
        params = {
            'type': 'actionStep',
            'limit': PAGE_SIZE,
            'skip': skip
        }

        try:
            response = requests.get(API_URL, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Handle different response formats
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get('data', data.get('results', data.get('items', [])))
                if not isinstance(records, list):
                    records = [data] if '_id' in data else []
            else:
                records = []

            if not records:
                logger.info(f"No more records at skip={skip}")
                break

            total_fetched += len(records)

            # Filter to current school year only
            current_year_records = [r for r in records if is_current_school_year(r)]
            all_records.extend(current_year_records)

            logger.info(f"Fetched {len(records)} records, {len(current_year_records)} from current school year (skip={skip}, total kept: {len(all_records)})")

            # Check if we got fewer records than requested (last page)
            if len(records) < PAGE_SIZE:
                break

            skip += PAGE_SIZE

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed at skip={skip}: {e}")
            raise

    logger.info(f"Total records from API: {total_fetched}, kept for current school year: {len(all_records)}")
    return all_records


def create_table_if_not_exists(client, table_ref):
    """Create the BigQuery table if it doesn't exist."""
    try:
        client.get_table(table_ref)
        logger.info(f"Table {table_ref} already exists")
    except NotFound:
        table = bigquery.Table(table_ref, schema=TABLE_SCHEMA)
        table.description = "Level Data Grow action step assignments synced from API"
        client.create_table(table)
        logger.info(f"Created table {table_ref}")


def load_to_bigquery(records):
    """Load records to BigQuery, replacing all existing data."""
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Create table if needed
    create_table_if_not_exists(client, table_ref)

    # Transform records
    sync_time = datetime.now(timezone.utc).isoformat()
    transformed = []
    for i, record in enumerate(records):
        try:
            transformed.append(transform_record(record, sync_time))
        except Exception as e:
            logger.warning(f"Failed to transform record {i} (_id={record.get('_id')}): {e}")

    logger.info(f"Transformed {len(transformed)} records")

    if not transformed:
        logger.warning("No records to load")
        return

    # Configure load job to replace existing data
    job_config = bigquery.LoadJobConfig(
        schema=TABLE_SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace table
    )

    # Load data
    logger.info(f"Loading {len(transformed)} records to BigQuery...")
    job = client.load_table_from_json(
        transformed,
        table_ref,
        job_config=job_config
    )

    # Wait for job to complete
    job.result()

    # Verify load
    table = client.get_table(table_ref)
    logger.info(f"Loaded {table.num_rows} rows to {table_ref}")


def main():
    """Main entry point."""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("Level Data Grow Action Steps Sync")
    logger.info(f"Started at: {start_time}")
    logger.info("=" * 60)

    try:
        # Get fresh access token
        token = get_access_token()

        # Fetch data from API
        records = fetch_all_records(token)

        if records:
            # Load to BigQuery
            load_to_bigquery(records)
            logger.info("Sync completed successfully!")
        else:
            logger.warning("No records fetched from API")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise

    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Duration: {duration}")
        logger.info("=" * 60)


if __name__ == '__main__':
    main()
