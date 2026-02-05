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
