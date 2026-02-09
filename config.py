"""
Configuration constants and environment variables.
No project imports — this is a leaf module.
"""

import os
import secrets

# Flask session
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# CORS
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')

# OAuth / domain
ALLOWED_DOMAIN = 'firstlineschools.org'
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Dev mode - bypasses OAuth for local testing
DEV_MODE = os.environ.get('FLASK_ENV') == 'development' or not GOOGLE_CLIENT_ID
DEV_USER_EMAIL = 'sshirey@firstlineschools.org'

# Admin emails - these users have access to ALL supervisors
ADMIN_EMAILS = [
    'sshirey@firstlineschools.org',      # Scott Shirey - Chief People Officer
    'brichardson@firstlineschools.org',  # Brittney Richardson - Chief of Human Resources
    'spence@firstlineschools.org',       # Sabrina Pence
    'mtoussaint@firstlineschools.org',   # M. Toussaint
    'csmith@firstlineschools.org',       # C. Smith
    'aleibfritz@firstlineschools.org',   # A. Leibfritz
    # CXO Team
    'sdomango@firstlineschools.org',     # Sivi Domango - Chief Experience Officer
    'dgoodwin@firstlineschools.org',     # Dawn Goodwin - K-8 Content Lead
    'rjohnson@firstlineschools.org',     # Rameisha Johnson - Manager Family Engagement
    'krodriguez@firstlineschools.org',   # Kristin Rodriguez - Dir of Culture
    'csteele@firstlineschools.org',      # Charlotte Steele - Dir of ESYNOLA
]

# Email aliases - map alternative emails to primary FirstLine emails
EMAIL_ALIASES = {
    'zach@esynola.org': 'zodonnell@firstlineschools.org',  # Zach O'Donnell
}

# Schools Dashboard role mapping by job title
SCHOOLS_DASHBOARD_ROLES = {
    'Chief Academic Officer': {'scope': 'all_except_cteam', 'label': 'Chief Academic Officer'},
    'ExDir of Teach and Learn': {'scope': 'teachers_only', 'label': 'ExDir of Teach and Learn'},
    'K-8 Content Lead': {'scope': 'teachers_only', 'label': 'K-8 Content Lead'},
}

# BigQuery configuration
PROJECT_ID = 'talent-demo-482004'
DATASET_ID = 'talent_grow_observations'
TABLE_ID = 'supervisor_dashboard_data'

# Kickboard
KICKBOARD_TABLE = 'fls-data-warehouse.kickboard.interactions'
KICKBOARD_ACL_TABLE = 'fls-data-warehouse.kickboard.interactions_acl'
KICKBOARD_ACL_RAW = 'fls-data-warehouse.acl.fls_acl_named'

KICKBOARD_SCHOOL_MAP = {
    'Ashe': 'Arthur Ashe Charter School',
    'LHA': 'Langston Hughes Academy',
    'Wheatley': 'Phillis Wheatley Community School',
    'Green': 'Samuel J. Green Charter School',
}

KICKBOARD_REVERSE_MAP = {v: k for k, v in KICKBOARD_SCHOOL_MAP.items()}

# Job titles that grant school-level Kickboard access
KICKBOARD_SCHOOL_LEADER_TITLES = [
    'principal',
    'assistant principal',
    'dean',
    'head of school',
    'director of culture',
]

# Current school year start date (first day of school)
CURRENT_SY_START = '2025-08-04'

# Suspensions Dashboard
SUSPENSIONS_ISS_TABLE = 'fls-data-warehouse.suspensions.iss_rates_25_26'
SUSPENSIONS_OSS_TABLE = 'fls-data-warehouse.suspensions.oss_rates_25_26'
SUSPENSIONS_SCHOOL_MAP = {
    'Ashe': 'Arthur Ashe Charter School',
    'LHA': 'Langston Hughes Academy',
    'Wheatley': 'Phillis Wheatley Community School',
    'Green': 'Samuel J. Green Charter School',
}
SUSPENSIONS_REVERSE_MAP = {v: k for k, v in SUSPENSIONS_SCHOOL_MAP.items()}
