"""
Shared authentication helpers.
Imports from config and extensions only (no circular deps).
"""

import logging
from functools import wraps
from flask import session, jsonify
from google.cloud import bigquery

from config import (
    ADMIN_EMAILS, CPO_EMAILS, HR_TEAM_EMAILS, SCHOOLS_TEAM_EMAILS,
    EMAIL_ALIASES, SCHOOLS_DASHBOARD_ROLES,
    KICKBOARD_SCHOOL_MAP, KICKBOARD_ACL_RAW, KICKBOARD_REVERSE_MAP,
    KICKBOARD_SCHOOL_LEADER_TITLES,
    SUSPENSIONS_SCHOOL_MAP, SUSPENSIONS_REVERSE_MAP,
    PROJECT_ID, DATASET_ID, TABLE_ID,
    POSITION_CONTROL_ROLES, ONBOARDING_ROLES,
)
from extensions import bq_client

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator to protect routes - requires valid session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def resolve_email_alias(email):
    """
    Resolve an email alias to the primary FirstLine email.
    Returns the primary email if an alias exists, otherwise returns the original email.
    """
    if not email:
        return email
    return EMAIL_ALIASES.get(email.lower(), email)


def is_cpo(email):
    """Check if user is CPO (Tier 1a) — full access to everything."""
    if not email:
        return False
    emails = [email.lower(), resolve_email_alias(email).lower()]
    return any(e in [x.lower() for x in CPO_EMAILS] for e in emails)


def is_hr_team(email):
    """Check if user is HR Team (Tier 1b) — Supervisor/HR/Staff List admin."""
    if not email:
        return False
    emails = [email.lower(), resolve_email_alias(email).lower()]
    return any(e in [x.lower() for x in HR_TEAM_EMAILS] for e in emails)


def is_hr_admin(email):
    """Check if user has HR admin access (CPO or HR Team)."""
    return is_cpo(email) or is_hr_team(email)


def is_schools_team(email):
    """Check if user is Schools Team — Schools/Kickboard/Suspensions admin."""
    if not email:
        return False
    emails = [email.lower(), resolve_email_alias(email).lower()]
    return any(e in [x.lower() for x in SCHOOLS_TEAM_EMAILS] for e in emails)


def is_schools_admin(email):
    """Check if user has schools admin access (CPO or Schools Team)."""
    return is_cpo(email) or is_schools_team(email)


def is_admin(email):
    """Check if user is admin (CPO or HR Team). Used for supervisor dashboard all-access."""
    return is_hr_admin(email)


def get_supervisor_name_for_email(email):
    """
    Look up supervisor name from BigQuery by email address.
    Returns the supervisor name if found, None otherwise.
    Checks both the original email and any alias.
    """
    if not bq_client or not email:
        return None

    primary_email = resolve_email_alias(email)

    emails_to_try = [primary_email]
    if email.lower() != primary_email.lower():
        emails_to_try.append(email)

    try:
        for try_email in emails_to_try:
            query = f"""
                SELECT DISTINCT Supervisor_Name__Unsecured_
                FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
                WHERE LOWER(Supervisor_Email) = LOWER(@email)
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", try_email)
                ]
            )
            query_job = bq_client.query(query, job_config=job_config)
            results = list(query_job.result())

            if results:
                logger.info(f"Found supervisor for email {email} (using {try_email}): {results[0].Supervisor_Name__Unsecured_}")
                return results[0].Supervisor_Name__Unsecured_

        return None
    except Exception as e:
        logger.error(f"Error looking up supervisor for email {email}: {e}")
        return None


def get_all_supervisors():
    """Get list of all unique supervisor names from BigQuery."""
    if not bq_client:
        return []

    try:
        query = f"""
            SELECT DISTINCT Supervisor_Name__Unsecured_
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            WHERE Supervisor_Name__Unsecured_ IS NOT NULL
            ORDER BY Supervisor_Name__Unsecured_
        """
        query_job = bq_client.query(query)
        results = query_job.result()
        return [row.Supervisor_Name__Unsecured_ for row in results]
    except Exception as e:
        logger.error(f"Error fetching all supervisors: {e}")
        return []


def get_accessible_supervisors(email, supervisor_name):
    """
    Get list of supervisors that the user can access.
    - Admins can access ALL supervisors
    - Regular supervisors can access their own team + all supervisors in their downline

    Uses recursive CTE to traverse the reporting hierarchy in staff_master_list.
    """
    if not bq_client:
        return []

    if is_admin(email):
        logger.info(f"Admin user {email} - granting access to all supervisors")
        return get_all_supervisors()

    if not supervisor_name:
        return []

    try:
        query = f"""
            WITH RECURSIVE
            supervisor_lookup AS (
                SELECT DISTINCT
                    Supervisor_Name__Unsecured_ AS supervisor_name,
                    Supervisor_Email AS supervisor_email
                FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
                WHERE Supervisor_Name__Unsecured_ IS NOT NULL
                AND Supervisor_Email IS NOT NULL
            ),
            staff_with_supervisor_format AS (
                SELECT
                    s.Email_Address AS employee_email,
                    s.Supervisor_Name__Unsecured_ AS reports_to,
                    sl.supervisor_name AS employee_supervisor_name
                FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` s
                LEFT JOIN supervisor_lookup sl ON LOWER(s.Email_Address) = LOWER(sl.supervisor_email)
                WHERE s.Supervisor_Name__Unsecured_ IS NOT NULL
                AND s.Employment_Status IN ('Active', 'Leave of absence')
            ),
            downline AS (
                SELECT @supervisor_name AS supervisor_name, 0 AS level

                UNION ALL

                SELECT sw.employee_supervisor_name AS supervisor_name, d.level + 1
                FROM staff_with_supervisor_format sw
                INNER JOIN downline d ON sw.reports_to = d.supervisor_name
                WHERE sw.employee_supervisor_name IS NOT NULL
                AND d.level < 10
            )
            SELECT DISTINCT supervisor_name
            FROM downline
            ORDER BY supervisor_name
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("supervisor_name", "STRING", supervisor_name)
            ]
        )

        logger.info(f"Fetching accessible supervisors for: {supervisor_name}")
        query_job = bq_client.query(query, job_config=job_config)
        results = query_job.result()

        accessible = [row.supervisor_name for row in results]
        logger.info(f"Found {len(accessible)} accessible supervisors for {supervisor_name}")
        return accessible

    except Exception as e:
        logger.error(f"Error fetching accessible supervisors for {supervisor_name}: {e}")
        return [supervisor_name] if supervisor_name else []


def get_schools_dashboard_role(email):
    """
    Determine if a user has access to the Schools Dashboard and what scope.
    Looks up their job title in staff_master_list_with_function.
    Returns: dict with 'has_access', 'scope', 'label' or None if no access.
    """
    if not email:
        return None

    primary_email = resolve_email_alias(email)
    if is_schools_admin(email):
        return {'has_access': True, 'scope': 'all_except_cteam', 'label': 'Admin'}

    if not bq_client:
        return None

    try:
        query = f"""
            SELECT Job_Title
            FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
            WHERE LOWER(Email_Address) = LOWER(@email)
            AND Employment_Status IN ('Active', 'Leave of absence')
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", primary_email)
            ]
        )
        results = list(bq_client.query(query, job_config=job_config).result())
        if not results:
            return None

        job_title = results[0].Job_Title or ''

        for role_title, role_info in SCHOOLS_DASHBOARD_ROLES.items():
            if role_title.lower() in job_title.lower():
                return {'has_access': True, 'scope': role_info['scope'], 'label': role_info['label']}

        return None
    except Exception as e:
        logger.error(f"Error checking schools dashboard role for {email}: {e}")
        return None


def get_kickboard_access(email):
    """
    Hybrid Kickboard access model:
    1. Admins → all schools, all data
    2. School Leaders (Principal, AP, Dean) → their school's full data
    3. Supervisors → data for interactions logged by staff in their downline
    4. ACL fallback → explicit school grants

    Returns: dict with access details or None if no access.
    """
    if not email:
        return None

    # 1. Schools admins (CPO + Schools Team) see everything
    if is_schools_admin(email):
        return {
            'has_access': True,
            'access_type': 'admin',
            'schools': list(KICKBOARD_SCHOOL_MAP.keys()),
            'staff_ids': None,  # None means all
            'school_map': KICKBOARD_SCHOOL_MAP,
            'label': 'Admin - All Schools'
        }

    if not bq_client:
        return None

    primary_email = resolve_email_alias(email)
    access_sources = []  # Track where access comes from
    schools_access = set()
    staff_ids_access = set()

    try:
        # Get user's job title, location, and name
        user_query = f"""
            SELECT
                Job_Title,
                Location,
                Employee_Number,
                Preferred_Name_Legal_Name
            FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
            WHERE LOWER(Email_Address) = LOWER(@email)
            AND Employment_Status IN ('Active', 'Leave of absence')
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", primary_email)
            ]
        )
        user_results = list(bq_client.query(user_query, job_config=job_config).result())

        if user_results:
            job_title = user_results[0].Job_Title or ''
            location = user_results[0].Location or ''
            user_name = user_results[0].Preferred_Name_Legal_Name or ''

            # 2. Check if school leader
            is_school_leader = any(
                title in job_title.lower()
                for title in KICKBOARD_SCHOOL_LEADER_TITLES
            )
            if is_school_leader and location:
                # Map location to school code
                school_code = KICKBOARD_REVERSE_MAP.get(location)
                if school_code:
                    schools_access.add(school_code)
                    access_sources.append(f'School Leader ({location})')
                    logger.info(f"Kickboard: {email} is school leader at {location}")

            # 3. Check if supervisor with downline staff
            if user_name:
                downline_query = f"""
                    WITH RECURSIVE downline AS (
                        -- Start with people who report directly to this user
                        SELECT
                            Employee_Number,
                            Preferred_Name_Legal_Name as name,
                            1 as level
                        FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
                        WHERE Supervisor_Name__Unsecured_ = @user_name
                        AND Employment_Status IN ('Active', 'Leave of absence')

                        UNION ALL

                        -- Recursively get people who report to the downline
                        SELECT
                            s.Employee_Number,
                            s.Preferred_Name_Legal_Name,
                            d.level + 1
                        FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` s
                        INNER JOIN downline d ON s.Supervisor_Name__Unsecured_ = d.name
                        WHERE s.Employment_Status IN ('Active', 'Leave of absence')
                        AND d.level < 10
                    )
                    SELECT DISTINCT Employee_Number
                    FROM downline
                    WHERE Employee_Number IS NOT NULL
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("user_name", "STRING", user_name)
                    ]
                )
                downline_results = list(bq_client.query(downline_query, job_config=job_config).result())

                if downline_results:
                    for row in downline_results:
                        if row.Employee_Number:
                            staff_ids_access.add(str(row.Employee_Number))
                    access_sources.append(f'Supervisor ({len(downline_results)} staff)')
                    logger.info(f"Kickboard: {email} has {len(downline_results)} staff in downline")

        # 4. ACL fallback - explicit school grants
        acl_query = f"""
            SELECT DISTINCT powerschool
            FROM `{KICKBOARD_ACL_RAW}`
            WHERE LOWER(email) = LOWER(@email)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", primary_email)
            ]
        )
        acl_results = list(bq_client.query(acl_query, job_config=job_config).result())

        for row in acl_results:
            if row.powerschool:
                schools_access.add(row.powerschool)
                if 'ACL' not in str(access_sources):
                    access_sources.append('ACL')

        # Build final access object
        if not schools_access and not staff_ids_access:
            logger.info(f"Kickboard: {email} has no access")
            return None

        # Build label
        label_parts = []
        if schools_access:
            school_names = [KICKBOARD_SCHOOL_MAP.get(s, s) for s in schools_access]
            label_parts.append(', '.join(school_names))
        if staff_ids_access and not schools_access:
            label_parts.append(f'Team ({len(staff_ids_access)} staff)')

        return {
            'has_access': True,
            'access_type': 'hybrid',
            'schools': list(schools_access) if schools_access else [],
            'staff_ids': list(staff_ids_access) if staff_ids_access else [],
            'school_map': KICKBOARD_SCHOOL_MAP,
            'label': ' | '.join(label_parts) if label_parts else 'Limited Access',
            'access_sources': access_sources
        }

    except Exception as e:
        logger.error(f"Error checking kickboard access for {email}: {e}")
        return None


def get_suspensions_access(email):
    """
    Suspensions dashboard access model (simplified from Kickboard):
    1. Admins → all schools
    2. School Leaders (Principal, AP, Dean) → their school only

    Returns: dict with access details or None if no access.
    """
    if not email:
        return None

    # 1. Schools admins (CPO + Schools Team) see everything
    if is_schools_admin(email):
        return {
            'has_access': True,
            'access_type': 'admin',
            'schools': list(SUSPENSIONS_SCHOOL_MAP.keys()),
            'school_map': SUSPENSIONS_SCHOOL_MAP,
            'label': 'Admin - All Schools'
        }

    if not bq_client:
        return None

    primary_email = resolve_email_alias(email)
    schools_access = set()

    try:
        # Get user's job title and location
        user_query = f"""
            SELECT
                Job_Title,
                Location
            FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
            WHERE LOWER(Email_Address) = LOWER(@email)
            AND Employment_Status IN ('Active', 'Leave of absence')
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", primary_email)
            ]
        )
        user_results = list(bq_client.query(user_query, job_config=job_config).result())

        if user_results:
            job_title = user_results[0].Job_Title or ''
            location = user_results[0].Location or ''

            # 2. Check if school leader
            is_school_leader = any(
                title in job_title.lower()
                for title in KICKBOARD_SCHOOL_LEADER_TITLES
            )
            if is_school_leader and location:
                # Map location to school code
                school_code = SUSPENSIONS_REVERSE_MAP.get(location)
                if school_code:
                    schools_access.add(school_code)
                    logger.info(f"Suspensions: {email} is school leader at {location}")

        if not schools_access:
            logger.info(f"Suspensions: {email} has no access")
            return None

        school_names = [SUSPENSIONS_SCHOOL_MAP.get(s, s) for s in schools_access]

        return {
            'has_access': True,
            'access_type': 'school_leader',
            'schools': list(schools_access),
            'school_map': SUSPENSIONS_SCHOOL_MAP,
            'label': ', '.join(school_names)
        }

    except Exception as e:
        logger.error(f"Error checking suspensions access for {email}: {e}")
        return None


def get_salary_access(email):
    """
    Salary Projection Dashboard access - C-Team only.
    Checks if user has 'Chief' or 'Ex. Dir' in their job title.
    No admin bypass - strictly job title based.

    Returns: dict with access details or None if no access.
    """
    if not email:
        return None

    if not bq_client:
        return None

    primary_email = resolve_email_alias(email)

    try:
        query = f"""
            SELECT Job_Title
            FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
            WHERE LOWER(Email_Address) = LOWER(@email)
            AND Employment_Status IN ('Active', 'Leave of absence')
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", primary_email)
            ]
        )
        results = list(bq_client.query(query, job_config=job_config).result())

        if not results:
            return None

        job_title = results[0].Job_Title or ''
        job_title_lower = job_title.lower()

        # Check for C-Team titles
        if 'chief' in job_title_lower or 'ex. dir' in job_title_lower or 'ex dir' in job_title_lower:
            logger.info(f"Salary access granted to {email} with title: {job_title}")
            return {
                'has_access': True,
                'access_type': 'cteam',
                'job_title': job_title,
                'label': job_title
            }

        logger.info(f"Salary access denied to {email} with title: {job_title}")
        return None

    except Exception as e:
        logger.error(f"Error checking salary access for {email}: {e}")
        return None


def compute_grade_band(grade_level_desc):
    """
    Map a Grade_Level_Desc value to a grade band bucket.
    Returns: 'Pre-K', 'K-2', '3-8', or None if not mappable.
    """
    if not grade_level_desc:
        return None

    val = grade_level_desc.strip().lower()

    # Pre-K
    if 'pre-k' in val or 'pk' in val or 'pre k' in val:
        return 'Pre-K'

    # K-2
    k2_values = [
        'kinder', 'kindergarten', 'k', '1', '2',
        'k thru 2', 'k-2', 'lower school', '1st', '2nd',
        'grade 1', 'grade 2', 'grade k',
    ]
    if val in k2_values:
        return 'K-2'
    if val in ['k&1', '1&2', 'k-1', '1-2', 'k thru 2']:
        return 'K-2'

    # 3-8
    three_eight_values = [
        '3', '4', '5', '6', '7', '8',
        '3rd', '4th', '5th', '6th', '7th', '8th',
        'grade 3', 'grade 4', 'grade 5', 'grade 6', 'grade 7', 'grade 8',
        'middle school', 'upper school',
    ]
    if val in three_eight_values:
        return '3-8'
    if any(val.startswith(p) for p in ['3-', '4-', '5-', '6-', '7-']) and val[-1].isdigit():
        return '3-8'
    if val in ['3&4', '5&6', '7&8', '3-5', '6-8', '3-8', '4-5', '4-6', '5-8']:
        return '3-8'

    return None


def map_grade_desc_to_levels(grade_level_desc):
    """
    Map a Grade_Level_Desc value to a list of integer grade levels for assessment matching.
    Returns a list of ints (e.g. [7, 8]), or None if the value means "all grades".
    """
    if not grade_level_desc:
        return None

    val = grade_level_desc.strip().lower()

    # Whole school / all grades → no filter
    if val in ('whole school', 'all grades', 'all'):
        return None

    # Pre-K / PK → grade 0
    if val in ('pre-k', 'pk', 'pre k', 'prek'):
        return [0]

    # Kindergarten → grade 0
    if val in ('k', 'kinder', 'kindergarten'):
        return [0]

    # Single grades 1-8
    single_map = {
        '1': [1], '1st': [1], 'grade 1': [1],
        '2': [2], '2nd': [2], 'grade 2': [2],
        '3': [3], '3rd': [3], 'grade 3': [3],
        '4': [4], '4th': [4], 'grade 4': [4],
        '5': [5], '5th': [5], 'grade 5': [5],
        '6': [6], '6th': [6], 'grade 6': [6],
        '7': [7], '7th': [7], 'grade 7': [7],
        '8': [8], '8th': [8], 'grade 8': [8],
    }
    if val in single_map:
        return single_map[val]

    # Multi-grade combos (explicit)
    combo_map = {
        'k&1': [0, 1], 'k-1': [0, 1],
        '1&2': [1, 2], '1-2': [1, 2],
        'k thru 2': [0, 1, 2], 'k-2': [0, 1, 2],
        '3&4': [3, 4], '3-4': [3, 4],
        '4&5': [4, 5], '4-5': [4, 5],
        '5&6': [5, 6], '5-6': [5, 6],
        '5&7': [5, 7],
        '6&7': [6, 7], '6-7': [6, 7],
        '7&8': [7, 8], '7-8': [7, 8],
        '3 thru 5': [3, 4, 5], '3-5': [3, 4, 5],
        '4-6': [4, 5, 6],
        '5-8': [5, 6, 7, 8],
        '6 thru 8': [6, 7, 8], '6-8': [6, 7, 8],
        '3 thru 8': [3, 4, 5, 6, 7, 8], '3-8': [3, 4, 5, 6, 7, 8],
    }
    if val in combo_map:
        return combo_map[val]

    # "N thru M" pattern (e.g. "4 thru 6")
    if ' thru ' in val:
        parts = val.split(' thru ')
        try:
            start = int(parts[0])
            end = int(parts[1])
            return list(range(start, end + 1))
        except (ValueError, IndexError):
            pass

    # "N&M" pattern for any two digits not already mapped
    if '&' in val:
        parts = val.split('&')
        try:
            return [int(p.strip()) for p in parts]
        except ValueError:
            pass

    # Middle school / upper school
    if val in ('middle school', 'upper school'):
        return [6, 7, 8]

    # Lower school
    if val in ('lower school',):
        return [0, 1, 2]

    # Unrecognized → no filter (match all)
    return None


def map_subject_desc_to_assessment(subject_desc):
    """
    Map a Subject_Desc value to a list of assessment Subject strings.
    Returns:
    - None if "All Subjects" or NULL (match all assessment subjects)
    - List of strings for known academic subjects (e.g. ['English'])
    - Empty list [] for non-academic subjects (PE, Art, etc.) → matches nothing
    """
    if not subject_desc:
        return None

    val = subject_desc.strip().lower()

    # "All Subjects" → match all
    if val in ('all subjects', 'all'):
        return None

    # Known academic subject mappings
    subject_map = {
        'ela': ['English'],
        'math': ['Math'],
        'algebra': ['Math'],
        'science': ['Science'],
        'social studies': ['Social Studies'],
        'science and social studies': ['Science', 'Social Studies'],
        'humanities': ['English', 'Social Studies'],
    }

    if val in subject_map:
        return subject_map[val]

    # Non-academic subjects → empty list (no assessment match)
    return []


def get_pcf_access(email):
    """Check if user has Position Control Form access."""
    email = (email or '').lower()
    return POSITION_CONTROL_ROLES.get(email)


def get_pcf_permissions(email):
    """Get the full permissions dict for a PCF user."""
    email = (email or '').lower()
    role_info = POSITION_CONTROL_ROLES.get(email)
    if not role_info:
        return None
    return {
        'role': role_info['role'],
        'can_approve': role_info['can_approve'],
        'can_edit_final': role_info['can_edit_final'],
        'can_create_position': role_info['can_create_position'],
        'can_edit_notes': role_info['role'] != 'viewer',
        'can_edit_dates': role_info['role'] in ('super_admin', 'hr'),
        'can_archive': role_info['role'] != 'viewer',
        'can_delete': role_info['role'] == 'super_admin',
        'is_viewer': role_info['role'] == 'viewer',
    }


def get_onboarding_access(email):
    """Check if user has Onboarding Form access."""
    email = (email or '').lower()
    return ONBOARDING_ROLES.get(email)


def get_onboarding_permissions(email):
    """Get the full permissions dict for an onboarding user."""
    email = (email or '').lower()
    role_info = ONBOARDING_ROLES.get(email)
    if not role_info:
        return None
    return {
        'role': role_info['role'],
        'can_edit': role_info['can_edit'],
        'can_delete': role_info['can_delete'],
        'can_archive': role_info['role'] != 'viewer',
        'is_viewer': role_info['role'] == 'viewer',
    }
