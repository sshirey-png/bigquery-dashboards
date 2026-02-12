#!/usr/bin/env python3
"""
Level Data Grow Meetings API to BigQuery Sync Script
Pulls meetings from the LDG API and loads them into BigQuery.
Automatically refreshes API token using client credentials.

Usage:
    python ldg_meetings_sync.py

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
        PROJECT_ID, DATASET_ID, PAGE_SIZE
    )
except ImportError:
    print("ERROR: ldg_config.py not found. Please create it with your credentials.")
    sys.exit(1)

# Meetings-specific configuration
TABLE_ID = "ldg_meetings"
API_URL = "https://grow-api.leveldata.com/external/meetings"
USERS_API_URL = "https://grow-api.leveldata.com/external/users"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Dynamic school year filter (July 1 - June 30)
_today = datetime.now(timezone.utc)
_sy_year = _today.year if _today.month >= 7 else _today.year - 1
SCHOOL_YEAR_START = datetime(_sy_year, 7, 1, tzinfo=timezone.utc)

# BigQuery table schema
TABLE_SCHEMA = [
    bigquery.SchemaField("_id", "STRING", mode="REQUIRED", description="Primary key"),
    bigquery.SchemaField("title", "STRING", mode="NULLABLE", description="Meeting title"),
    bigquery.SchemaField("date", "TIMESTAMP", mode="NULLABLE", description="Meeting date"),
    bigquery.SchemaField("creator_id", "STRING", mode="NULLABLE", description="Creator user ID"),
    bigquery.SchemaField("creator_name", "STRING", mode="NULLABLE", description="Creator full name"),
    bigquery.SchemaField("creator_email", "STRING", mode="NULLABLE", description="Creator email"),
    bigquery.SchemaField("type_id", "STRING", mode="NULLABLE", description="Meeting type ID"),
    bigquery.SchemaField("type_name", "STRING", mode="NULLABLE", description="Meeting type name"),
    bigquery.SchemaField("school_id", "STRING", mode="NULLABLE", description="School ID"),
    bigquery.SchemaField("course_id", "STRING", mode="NULLABLE", description="Course ID"),
    bigquery.SchemaField("grade_id", "STRING", mode="NULLABLE", description="Grade ID"),
    bigquery.SchemaField("participant_count", "INTEGER", mode="NULLABLE", description="Number of participants"),
    bigquery.SchemaField("participant_ids", "STRING", mode="NULLABLE", description="Comma-separated participant user IDs"),
    bigquery.SchemaField("participant_names", "STRING", mode="NULLABLE", description="Comma-separated participant names"),
    bigquery.SchemaField("participant_emails", "STRING", mode="NULLABLE", description="Comma-separated participant emails"),
    bigquery.SchemaField("what_was_discussed", "STRING", mode="NULLABLE", description="Discussion notes (HTML stripped)"),
    bigquery.SchemaField("next_steps", "STRING", mode="NULLABLE", description="Next steps (HTML stripped)"),
    bigquery.SchemaField("private", "BOOLEAN", mode="NULLABLE", description="Is private"),
    bigquery.SchemaField("locked", "BOOLEAN", mode="NULLABLE", description="Is locked"),
    bigquery.SchemaField("signatureRequired", "BOOLEAN", mode="NULLABLE", description="Signature required"),
    bigquery.SchemaField("isTemplate", "BOOLEAN", mode="NULLABLE", description="Is template"),
    bigquery.SchemaField("isWeeklyDataMeeting", "BOOLEAN", mode="NULLABLE", description="Is weekly data meeting"),
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


def extract_additional_field(additional_fields, field_name):
    """Extract content from additionalFields by field name."""
    if not additional_fields or not isinstance(additional_fields, list):
        return None

    for field in additional_fields:
        if isinstance(field, dict) and field.get('name') == field_name:
            content = field.get('content')
            if content:
                return strip_html(content)
    return None


def extract_participant_ids(participants):
    """Extract participant user IDs as comma-separated string."""
    if not participants or not isinstance(participants, list):
        return None

    ids = []
    for p in participants:
        if isinstance(p, dict) and 'user' in p:
            ids.append(p['user'])
    return ', '.join(ids) if ids else None


def extract_participant_info(participants, user_lookup):
    """Extract participant names and emails using user lookup."""
    if not participants or not isinstance(participants, list):
        return None, None

    names = []
    emails = []
    for p in participants:
        if isinstance(p, dict) and 'user' in p:
            user_id = p['user']
            user = user_lookup.get(user_id, {})
            if user.get('name'):
                names.append(user['name'])
            if user.get('email'):
                emails.append(user['email'])

    return (
        ', '.join(names) if names else None,
        ', '.join(emails) if emails else None
    )


def fetch_all_users(token):
    """Fetch all users from the API to build a lookup dictionary."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    user_lookup = {}
    skip = 0

    logger.info("Fetching users for participant lookup...")

    while True:
        params = {'limit': PAGE_SIZE, 'skip': skip}

        try:
            response = requests.get(USERS_API_URL, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and 'data' in data:
                users = data.get('data', [])
            elif isinstance(data, list):
                users = data
            else:
                users = []

            if not users:
                break

            for user in users:
                user_id = user.get('_id')
                if user_id:
                    user_lookup[user_id] = {
                        'name': user.get('name'),
                        'email': user.get('email')
                    }

            if len(users) < PAGE_SIZE:
                break

            skip += PAGE_SIZE

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch users at skip={skip}: {e}")
            break

    logger.info(f"Loaded {len(user_lookup)} users for lookup")
    return user_lookup


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


def transform_record(record, sync_time, user_lookup):
    """Transform API record to BigQuery row format."""
    creator = record.get('creator', {}) or {}
    meeting_type = record.get('type', {}) or {}
    participants = record.get('participants', []) or []
    additional_fields = record.get('additionalFields', []) or []

    participant_names, participant_emails = extract_participant_info(participants, user_lookup)

    return {
        '_id': record.get('_id'),
        'title': record.get('title'),
        'date': parse_timestamp(record.get('date')),
        'creator_id': creator.get('_id'),
        'creator_name': creator.get('name'),
        'creator_email': creator.get('email'),
        'type_id': meeting_type.get('_id'),
        'type_name': meeting_type.get('name'),
        'school_id': record.get('school'),
        'course_id': record.get('course'),
        'grade_id': record.get('grade'),
        'participant_count': len(participants),
        'participant_ids': extract_participant_ids(participants),
        'participant_names': participant_names,
        'participant_emails': participant_emails,
        'what_was_discussed': extract_additional_field(additional_fields, 'What was discussed?'),
        'next_steps': extract_additional_field(additional_fields, 'What are the next steps?'),
        'private': record.get('private'),
        'locked': record.get('locked'),
        'signatureRequired': record.get('signatureRequired'),
        'isTemplate': record.get('isTemplate'),
        'isWeeklyDataMeeting': record.get('isWeeklyDataMeeting'),
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
            'archived': 'false',
            'limit': PAGE_SIZE,
            'skip': skip
        }

        try:
            response = requests.get(API_URL, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Handle response format: {"data": [...], "count": N, "limit": N, "skip": N}
            if isinstance(data, dict) and 'data' in data:
                records = data.get('data', [])
            elif isinstance(data, list):
                records = data
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
        table.description = "Level Data Grow meetings synced from API"
        client.create_table(table)
        logger.info(f"Created table {table_ref}")


def load_to_bigquery(records, user_lookup):
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
            transformed.append(transform_record(record, sync_time, user_lookup))
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
    logger.info("Level Data Grow Meetings Sync")
    logger.info(f"Started at: {start_time}")
    logger.info("=" * 60)

    try:
        # Get fresh access token
        token = get_access_token()

        # Fetch users for participant lookup
        user_lookup = fetch_all_users(token)

        # Fetch data from API
        records = fetch_all_records(token)

        if records:
            # Load to BigQuery
            load_to_bigquery(records, user_lookup)
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
