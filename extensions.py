"""
Shared extension objects: BigQuery client and OAuth.
Imports only from config (no circular deps).
"""

import logging
from google.cloud import bigquery
from authlib.integrations.flask_client import OAuth

from config import PROJECT_ID

logger = logging.getLogger(__name__)

# BigQuery client — initialized at import time (same as before)
try:
    bq_client = bigquery.Client(project=PROJECT_ID)
    logger.info(f"BigQuery client initialized for project: {PROJECT_ID}")
except Exception as e:
    logger.error(f"Failed to initialize BigQuery client: {e}")
    bq_client = None

# OAuth object — call oauth.init_app(app) inside create_app()
oauth = OAuth()

# Cached school start date from ADA table
_school_start_cache = {}


def get_school_start_date():
    """Get the first day of school for the current school year from the ADA table.
    Caches the result so BigQuery is only queried once per school year."""
    from config import CURRENT_SY_START
    sy_year = CURRENT_SY_START[:4]  # e.g., "2025"

    if sy_year in _school_start_cache:
        return _school_start_cache[sy_year]

    if not bq_client:
        return f"{sy_year}-08-01"

    try:
        query = """
            SELECT MIN(Calendar_Date) as first_day
            FROM `fls-data-warehouse.attendance.ada_adm`
            WHERE school_year = @sy_year
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("sy_year", "INT64", int(sy_year))
            ]
        )
        results = list(bq_client.query(query, job_config=job_config).result())
        if results and results[0].first_day:
            date_str = results[0].first_day.isoformat()
            _school_start_cache[sy_year] = date_str
            return date_str
    except Exception as e:
        logger.warning(f"Failed to fetch school start date from ADA table: {e}")

    # Fallback to August 1
    fallback = f"{sy_year}-08-01"
    _school_start_cache[sy_year] = fallback
    return fallback
