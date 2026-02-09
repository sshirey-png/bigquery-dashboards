"""
Shared authentication helpers.
Imports from config and extensions only (no circular deps).
"""

import logging
from functools import wraps
from flask import session, jsonify
from google.cloud import bigquery

from config import (
    ADMIN_EMAILS, EMAIL_ALIASES, SCHOOLS_DASHBOARD_ROLES,
    KICKBOARD_SCHOOL_MAP, KICKBOARD_ACL_RAW, KICKBOARD_REVERSE_MAP,
    KICKBOARD_SCHOOL_LEADER_TITLES,
    SUSPENSIONS_SCHOOL_MAP, SUSPENSIONS_REVERSE_MAP,
    PROJECT_ID, DATASET_ID, TABLE_ID,
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


def is_admin(email):
    """Check if the user is an admin with full access. Also checks email aliases."""
    if not email:
        return False
    emails_to_check = [email.lower(), resolve_email_alias(email).lower()]
    admin_emails_lower = [e.lower() for e in ADMIN_EMAILS]
    return any(e in admin_emails_lower for e in emails_to_check)


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
    if is_admin(email):
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

    # 1. Admins see everything
    if is_admin(email):
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

    # 1. Admins see everything
    if is_admin(email):
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
