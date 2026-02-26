"""
Configuration constants and environment variables.
No project imports — this is a leaf module.
"""

import os
import secrets
from datetime import date, datetime

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

# ── Role-Based Access (by job title from BigQuery) ──

# Tier 1a: CPO — full access to everything
CPO_TITLE = 'Chief People Officer'

# Tier 1b: HR Team — Supervisor, HR, Staff List admin access
HR_TEAM_TITLES = [
    'Chief Executive Officer',
    'Chief HR Officer',
    'Manager, HR',
    'Manager Payroll',
    'Manager - Benefits',
]

# Schools Team — Schools, Kickboard, Suspensions admin access
SCHOOLS_TEAM_TITLES = [
    'Chief Experience Officer',
    'K-8 Content Lead',
    'Dir of Culture',
    'Dir of ESYNOLA',
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

# Dynamic school year calculation (July 1 - June 30)
# If today is before July, we're in last year's school year; otherwise this year's
_today = date.today()
_sy_year = _today.year if _today.month >= 7 else _today.year - 1
CURRENT_SY_START = f'{_sy_year}-07-01'
CURRENT_SY_LABEL = f'{_sy_year}-{str(_sy_year + 1)[-2:]}'
CURRENT_SY_END = f'{_sy_year + 1}-06-30'

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

# Performance Matters (Assessment Fidelity)
PM_RESULTS_BY_TEST = 'fls-data-warehouse.performance_matters.results_by_test'
PM_RESULTS_RAW = 'fls-data-warehouse.performance_matters.results_raw'

# SPS — Bottom 25th percentile students
SPS_BOTTOM_25 = 'fls-data-warehouse.sps.24_25_bottom_25'

# Student Rosters & Class Schedules
STUDENT_ROSTER = 'fls-data-warehouse.student_rosters.student_roster'
CLASS_SCHEDULES = 'fls-data-warehouse.class_schedules.class_schedules'

# ── Staffing Board — read access by job title ──
# C-Team titles use a contains-match ("Chief" or "ExDir"), same as salary dashboard
STAFFING_BOARD_C_TEAM_KEYWORDS = ['Chief', 'ExDir']
# Additional titles that get Staffing Board read access beyond C-Team
STAFFING_BOARD_EXTRA_TITLES = [
    'School Director',
    'Manager, HR',
    'Manager Payroll',
    'Manager Finance',
    'Talent Operations Manager',
    'Recruitment Manager',
]

# ── Position Control Form — permissions by job title ──
POSITION_CONTROL_TITLE_ROLES = {
    'Chief People Officer': {'role': 'super_admin', 'can_approve': ['ceo_approval', 'finance_approval', 'talent_approval', 'hr_approval'], 'can_edit_final': True, 'can_create_position': True},
    'Chief Executive Officer': {'role': 'ceo', 'can_approve': ['ceo_approval'], 'can_edit_final': True, 'can_create_position': False},
    'Chief Operating Officer': {'role': 'finance', 'can_approve': ['finance_approval'], 'can_edit_final': False, 'can_create_position': False},
    'Manager Finance': {'role': 'finance', 'can_approve': ['finance_approval'], 'can_edit_final': False, 'can_create_position': False},
    'Manager Payroll': {'role': 'viewer', 'can_approve': [], 'can_edit_final': False, 'can_create_position': False},
    'Chief HR Officer': {'role': 'hr', 'can_approve': ['hr_approval', 'talent_approval'], 'can_edit_final': True, 'can_create_position': True},
    'Manager, HR': {'role': 'hr', 'can_approve': ['hr_approval'], 'can_edit_final': False, 'can_create_position': False},
    'School Director': {'role': 'viewer', 'can_approve': [], 'can_edit_final': False, 'can_create_position': False},
    'Talent Operations Manager': {'role': 'viewer', 'can_approve': [], 'can_edit_final': False, 'can_create_position': False},
    'Recruitment Manager': {'role': 'viewer', 'can_approve': [], 'can_edit_final': False, 'can_create_position': False},
    'Manager - Benefits': {'role': 'viewer', 'can_approve': [], 'can_edit_final': False, 'can_create_position': False},
}

PCF_DATASET_ID = 'position_control_form'
PCF_TABLE_ID = 'requests'
PC_DATASET_ID = 'talent_grow_observations'
PC_TABLE_ID = 'position_control'

# ── Onboarding Form — permissions by job title ──
ONBOARDING_TITLE_ROLES = {
    'Chief People Officer': {'role': 'super_admin', 'can_edit': True, 'can_delete': True},
    'Chief HR Officer': {'role': 'hr', 'can_edit': True, 'can_delete': False},
    'Manager, HR': {'role': 'hr', 'can_edit': True, 'can_delete': False},
    'Manager Payroll': {'role': 'viewer', 'can_edit': False, 'can_delete': False},
}

ONBOARDING_DATASET_ID = 'onboarding_form'
ONBOARDING_TABLE_ID = 'submissions'

# ── Email (SMTP) ──
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'talent@firstlineschools.org')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
