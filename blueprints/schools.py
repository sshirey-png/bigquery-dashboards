"""Schools Dashboard routes."""

import os
import logging
from flask import Blueprint, jsonify, request, session, send_from_directory
from google.cloud import bigquery

from config import PROJECT_ID, DATASET_ID, TABLE_ID, CURRENT_SY_START
from extensions import bq_client
from auth import login_required, get_schools_dashboard_role, compute_grade_band

logger = logging.getLogger(__name__)

bp = Blueprint('schools', __name__)

HTML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@bp.route('/schools-dashboard')
def schools_dashboard():
    """Serve the Schools Dashboard HTML file"""
    return send_from_directory(HTML_DIR, 'schools-dashboard.html')


@bp.route('/api/schools/staff', methods=['GET'])
@login_required
def get_schools_staff():
    """
    Get staff data for the Schools Dashboard.
    Role-based scoping: teachers_only or all_except_cteam.
    Excludes sensitive HR data (PMAP, ITR, IAP/Write-ups).
    Query params: location, supervisor, employee_type, job_function, subject, grade_band
    """
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    schools_role = get_schools_dashboard_role(user_email)

    if not schools_role:
        return jsonify({'error': 'Access denied. Schools Dashboard access required.'}), 403

    scope = schools_role['scope']

    location_filter = request.args.get('location', '')
    supervisor_filter = request.args.get('supervisor', '')
    employee_type_filter = request.args.get('employee_type', '')
    job_function_filter = request.args.get('job_function', '')
    subject_filter = request.args.get('subject', '')
    grade_band_filter = request.args.get('grade_band', '')

    try:
        scope_filter = ""
        if scope == 'teachers_only':
            scope_filter = "AND s.Job_Function = 'Teacher'"
        elif scope == 'all_except_cteam':
            scope_filter = "AND sml.Job_Title NOT LIKE '%Chief%' AND sml.Job_Title NOT LIKE '%CEO%'"

        query = f"""
            WITH latest_accruals AS (
                SELECT
                    `Person Number` as Person_Number,
                    `Accrual Code Name` as Accrual_Code_Name,
                    (`Earned to Date _Hours_` + `Pending Grants _Hours_`) as max_hours,
                    (`Earned to Date _Hours_` + `Pending Grants _Hours_` - COALESCE(`Taken to Date _Hours_`, 0)) as remaining_hours
                FROM `{PROJECT_ID}.payroll_validation.accrual_balance`
                WHERE `Date Balance as of Date` = (
                    SELECT MAX(`Date Balance as of Date`)
                    FROM `{PROJECT_ID}.payroll_validation.accrual_balance`
                )
            ),
            accrual_pivoted AS (
                SELECT
                    Person_Number,
                    MAX(CASE WHEN Accrual_Code_Name = 'PTO' THEN remaining_hours END) as pto_available,
                    MAX(CASE WHEN Accrual_Code_Name = 'PTO' THEN max_hours END) as pto_max,
                    MAX(CASE WHEN Accrual_Code_Name = 'Vacation' THEN remaining_hours END) as vacation_available,
                    MAX(CASE WHEN Accrual_Code_Name = 'Vacation' THEN max_hours END) as vacation_max,
                    MAX(CASE WHEN Accrual_Code_Name = 'Personal Time' THEN remaining_hours END) as personal_available,
                    MAX(CASE WHEN Accrual_Code_Name = 'Personal Time' THEN max_hours END) as personal_max,
                    MAX(CASE WHEN Accrual_Code_Name = 'Sick' THEN remaining_hours END) as sick_available,
                    MAX(CASE WHEN Accrual_Code_Name = 'Sick' THEN max_hours END) as sick_max
                FROM latest_accruals
                GROUP BY Person_Number
            ),
            published_obs_counts AS (
                SELECT
                    teacher_internal_id,
                    COUNT(*) as total_published
                FROM (
                    SELECT DISTINCT
                        teacher_internal_id,
                        observation_type,
                        observed_at,
                        observer_name,
                        rubric_form
                    FROM `{PROJECT_ID}.{DATASET_ID}.observations_raw_native`
                    WHERE teacher_internal_id IS NOT NULL
                    AND is_published = 1
                    AND observed_at >= '{CURRENT_SY_START}'
                )
                GROUP BY teacher_internal_id
            )
            SELECT
                s.Employee_Number,
                s.first_name,
                s.last_name,
                s.Email_Address,
                FORMAT_DATE('%%m-%%d', s.Date_of_Birth) as birthday_month_day,
                s.Location_Name,
                s.Supervisor_Name__Unsecured_,
                s.job_title,
                s.Employment_Status,
                s.Last_Hire_Date,
                s.Job_Function,
                s.years_of_service,
                COALESCE(poc.total_published, 0) as total_observations,
                s.last_observation_date,
                s.last_observation_type,
                CONCAT(s.first_name, ' ', s.last_name) AS Staff_Name,
                a.pto_available,
                a.pto_max,
                a.vacation_available,
                a.vacation_max,
                a.personal_available,
                a.personal_max,
                a.sick_available,
                a.sick_max,
                sml.Salary_or_Hourly,
                sml.Subject_Desc,
                sml.Grade_Level_Desc
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` s
            LEFT JOIN accrual_pivoted a ON s.Employee_Number = a.Person_Number
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` sml
                ON LOWER(s.Email_Address) = LOWER(sml.Email_Address)
            LEFT JOIN published_obs_counts poc
                ON s.Employee_Number = CAST(poc.teacher_internal_id AS INT64)
            WHERE 1=1
                {scope_filter}
                {f"AND s.Location_Name = @location" if location_filter else ""}
                {f"AND s.Supervisor_Name__Unsecured_ = @supervisor" if supervisor_filter else ""}
                {f"AND sml.Salary_or_Hourly = @employee_type" if employee_type_filter else ""}
                {f"AND s.Job_Function = @job_function" if job_function_filter else ""}
                {f"AND sml.Subject_Desc = @subject" if subject_filter else ""}
            ORDER BY s.Location_Name, s.last_name, s.first_name
        """

        params = []
        if location_filter:
            params.append(bigquery.ScalarQueryParameter("location", "STRING", location_filter))
        if supervisor_filter:
            params.append(bigquery.ScalarQueryParameter("supervisor", "STRING", supervisor_filter))
        if employee_type_filter:
            params.append(bigquery.ScalarQueryParameter("employee_type", "STRING", employee_type_filter))
        if job_function_filter:
            params.append(bigquery.ScalarQueryParameter("job_function", "STRING", job_function_filter))
        if subject_filter:
            params.append(bigquery.ScalarQueryParameter("subject", "STRING", subject_filter))

        job_config = bigquery.QueryJobConfig(query_parameters=params)

        logger.info(f"Schools Dashboard: Fetching staff data with scope={scope}")
        query_job = bq_client.query(query, job_config=job_config)
        results = query_job.result()

        staff_data = []
        for row in results:
            staff_member = dict(row.items())

            grade_level_desc = staff_member.get('Grade_Level_Desc', '')
            staff_member['grade_band'] = compute_grade_band(grade_level_desc)

            for key, value in staff_member.items():
                if hasattr(value, 'isoformat'):
                    staff_member[key] = value.isoformat()

            staff_data.append(staff_member)

        if grade_band_filter:
            staff_data = [s for s in staff_data if s.get('grade_band') == grade_band_filter]

        logger.info(f"Schools Dashboard: Found {len(staff_data)} staff members")
        return jsonify(staff_data)

    except Exception as e:
        logger.error(f"Error fetching schools staff: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/schools/filter-options', methods=['GET'])
@login_required
def get_schools_filter_options():
    """
    Get available filter options for the Schools Dashboard.
    Returns distinct values scoped by the user's role.
    """
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    schools_role = get_schools_dashboard_role(user_email)

    if not schools_role:
        return jsonify({'error': 'Access denied. Schools Dashboard access required.'}), 403

    scope = schools_role['scope']

    try:
        scope_filter = ""
        if scope == 'teachers_only':
            scope_filter = "AND s.Job_Function = 'Teacher'"
        elif scope == 'all_except_cteam':
            scope_filter = "AND sml.Job_Title NOT LIKE '%Chief%' AND sml.Job_Title NOT LIKE '%CEO%'"

        query = f"""
            SELECT DISTINCT
                s.Location_Name,
                s.Supervisor_Name__Unsecured_,
                sml.Salary_or_Hourly,
                s.Job_Function,
                sml.Subject_Desc,
                sml.Grade_Level_Desc
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` s
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` sml
                ON LOWER(s.Email_Address) = LOWER(sml.Email_Address)
            WHERE s.Location_Name IS NOT NULL
                {scope_filter}
        """

        results = bq_client.query(query).result()

        locations = set()
        supervisors = set()
        employee_types = set()
        job_functions = set()
        subjects = set()
        grade_bands = set()

        for row in results:
            if row.Location_Name:
                locations.add(row.Location_Name)
            if row.Supervisor_Name__Unsecured_:
                supervisors.add(row.Supervisor_Name__Unsecured_)
            if row.Salary_or_Hourly:
                employee_types.add(row.Salary_or_Hourly)
            if row.Job_Function:
                job_functions.add(row.Job_Function)
            if row.Subject_Desc:
                subjects.add(row.Subject_Desc)
            if row.Grade_Level_Desc:
                band = compute_grade_band(row.Grade_Level_Desc)
                if band:
                    grade_bands.add(band)

        return jsonify({
            'locations': sorted(list(locations)),
            'supervisors': sorted(list(supervisors)),
            'employee_types': sorted(list(employee_types)),
            'job_functions': sorted(list(job_functions)),
            'subjects': sorted(list(subjects)),
            'grade_bands': sorted(list(grade_bands))
        })

    except Exception as e:
        logger.error(f"Error fetching schools filter options: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/schools/action-steps', methods=['GET'])
@login_required
def get_schools_action_steps():
    """
    Get action steps for staff in the Schools Dashboard scope.
    Returns a dict of email -> action step info.
    """
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    schools_role = get_schools_dashboard_role(user_email)

    if not schools_role:
        return jsonify({'error': 'Access denied. Schools Dashboard access required.'}), 403

    scope = schools_role['scope']

    try:
        scope_filter = ""
        if scope == 'teachers_only':
            scope_filter = "AND s.Job_Function = 'Teacher'"
        elif scope == 'all_except_cteam':
            scope_filter = "AND s.Job_Title NOT LIKE '%Chief%' AND s.Job_Title NOT LIKE '%CEO%'"

        query = f"""
            SELECT
                a._id,
                a.name,
                a.user_email,
                a.user_name,
                a.creator_name,
                a.creator_email,
                a.progress_percent,
                a.tags,
                a.created,
                a.lastModified
            FROM `{PROJECT_ID}.{DATASET_ID}.ldg_action_steps` a
            INNER JOIN `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` s
                ON LOWER(a.user_email) = LOWER(s.Email_Address)
            WHERE s.Employment_Status IN ('Active', 'Leave of absence')
            AND a.archivedAt IS NULL
            AND a.created >= '{CURRENT_SY_START}'
            {scope_filter}
            ORDER BY a.user_email, a.created DESC
        """

        logger.info("Schools Dashboard: Fetching action steps")
        query_job = bq_client.query(query)
        results = query_job.result()

        action_steps = {}
        for row in results:
            email = row.user_email.lower() if row.user_email else ''
            step = {
                'id': row._id,
                'name': row.name,
                'user_name': row.user_name,
                'creator_name': row.creator_name,
                'creator_email': row.creator_email,
                'progress_percent': row.progress_percent,
                'tags': row.tags,
                'created': row.created.isoformat() if row.created else None,
                'lastModified': row.lastModified.isoformat() if row.lastModified else None
            }
            if email not in action_steps:
                action_steps[email] = []
            action_steps[email].append(step)

        logger.info(f"Schools Dashboard: Found action steps for {len(action_steps)} staff members")
        return jsonify(action_steps)

    except Exception as e:
        logger.error(f"Error fetching schools action steps: {e}")
        return jsonify({'error': str(e)}), 500
