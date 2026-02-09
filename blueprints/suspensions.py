"""Suspensions Dashboard routes."""

import os
import logging
from flask import Blueprint, jsonify, request, session, send_from_directory
from google.cloud import bigquery

from config import (
    SUSPENSIONS_ISS_TABLE, SUSPENSIONS_OSS_TABLE, SUSPENSIONS_SCHOOL_MAP,
    CURRENT_SY_START,
)
from extensions import bq_client
from auth import login_required, get_suspensions_access

logger = logging.getLogger(__name__)

bp = Blueprint('suspensions', __name__)

HTML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_access_condition(access):
    """
    Build access conditions based on user's access level.
    - Admin: no filter (see all)
    - School leader: filter by their school(s)

    Returns (conditions_list, params_list).
    """
    conditions = ["Enroll_Status = 0"]  # Active students only
    params = []

    if access.get('access_type') == 'admin':
        return conditions, params

    schools = access.get('schools', [])
    if schools:
        school_placeholders = ', '.join([f'@school_{i}' for i in range(len(schools))])
        conditions.append(f"School_Short_Name IN ({school_placeholders})")
        for i, school in enumerate(schools):
            params.append(bigquery.ScalarQueryParameter(f"school_{i}", "STRING", school))

    return conditions, params


@bp.route('/suspensions-dashboard')
def suspensions_dashboard():
    """Serve the Suspensions Dashboard HTML file"""
    return send_from_directory(HTML_DIR, 'suspensions-dashboard.html')


@bp.route('/api/suspensions/summary', methods=['GET'])
@login_required
def suspensions_summary():
    """
    Network-level summary for the Suspensions dashboard.
    Returns per-school ISS/OSS metrics and network totals.
    """
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    access = get_suspensions_access(user_email)

    if not access:
        return jsonify({'error': 'Access denied. Suspensions Dashboard access required.'}), 403

    acl_conds, acl_params = _get_access_condition(access)

    # Optional filters
    school = request.args.get('school', '')
    grade = request.args.get('grade', '')
    suspension_type = request.args.get('type', '')  # iss, oss, or blank for both
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    # Build conditions for ISS and OSS queries
    iss_conditions = list(acl_conds)
    oss_conditions = list(acl_conds)
    params = list(acl_params)

    if school:
        iss_conditions.append("School_Short_Name = @school")
        oss_conditions.append("School_Short_Name = @school")
        params.append(bigquery.ScalarQueryParameter("school", "STRING", school))
    if grade:
        iss_conditions.append("Grade_Level = @grade")
        oss_conditions.append("Grade_Level = @grade")
        params.append(bigquery.ScalarQueryParameter("grade", "INT64", int(grade)))
    if date_from:
        iss_conditions.append("CAST(Incident_Date AS DATE) >= @date_from")
        oss_conditions.append("CAST(Incident_Date AS DATE) >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "DATE", date_from))
    if date_to:
        iss_conditions.append("CAST(Incident_Date AS DATE) <= @date_to")
        oss_conditions.append("CAST(Incident_Date AS DATE) <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "DATE", date_to))

    iss_where = " AND ".join(iss_conditions) if iss_conditions else "1=1"
    oss_where = " AND ".join(oss_conditions) if oss_conditions else "1=1"

    try:
        # Build query based on suspension type filter
        if suspension_type == 'iss':
            query = f"""
                SELECT
                    School_Short_Name as school,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {iss_where}
                GROUP BY School_Short_Name
            """
        elif suspension_type == 'oss':
            query = f"""
                SELECT
                    School_Short_Name as school,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {oss_where}
                GROUP BY School_Short_Name
            """
        else:
            # Both ISS and OSS
            query = f"""
                SELECT
                    School_Short_Name as school,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {iss_where}
                GROUP BY School_Short_Name

                UNION ALL

                SELECT
                    School_Short_Name as school,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {oss_where}
                GROUP BY School_Short_Name
            """

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = list(bq_client.query(query, job_config=job_config).result())

        # Aggregate by school
        school_data = {}
        for row in results:
            school_code = row.school
            if school_code not in school_data:
                school_data[school_code] = {
                    'school': school_code,
                    'full_name': SUSPENSIONS_SCHOOL_MAP.get(school_code, school_code),
                    'iss_count': 0,
                    'oss_count': 0,
                    'iss_days': 0,
                    'oss_days': 0,
                    'iss_students': 0,
                    'oss_students': 0,
                }

            if row.type == 'ISS':
                school_data[school_code]['iss_count'] = row.incident_count or 0
                school_data[school_code]['iss_days'] = float(row.total_days or 0)
                school_data[school_code]['iss_students'] = row.students_affected or 0
            else:
                school_data[school_code]['oss_count'] = row.incident_count or 0
                school_data[school_code]['oss_days'] = float(row.total_days or 0)
                school_data[school_code]['oss_students'] = row.students_affected or 0

        # Calculate totals for each school
        schools = []
        for code, data in school_data.items():
            data['total_incidents'] = data['iss_count'] + data['oss_count']
            data['total_days'] = data['iss_days'] + data['oss_days']
            schools.append(data)

        schools.sort(key=lambda x: x['school'])

        # Network totals
        network_totals = {
            'iss_count': sum(s['iss_count'] for s in schools),
            'oss_count': sum(s['oss_count'] for s in schools),
            'total_incidents': sum(s['total_incidents'] for s in schools),
            'total_days': sum(s['total_days'] for s in schools),
            'iss_days': sum(s['iss_days'] for s in schools),
            'oss_days': sum(s['oss_days'] for s in schools),
        }

        # Get unique students affected across network (need separate query)
        students_query = f"""
            SELECT COUNT(DISTINCT student_number) as unique_students
            FROM (
                SELECT Student_Number as student_number
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {iss_where}
                UNION DISTINCT
                SELECT Student_Number as student_number
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {oss_where}
            )
        """
        students_result = list(bq_client.query(students_query, job_config=job_config).result())
        network_totals['students_affected'] = students_result[0].unique_students if students_result else 0

        logger.info(f"Suspensions summary: {len(schools)} schools for {user_email}")
        return jsonify({'schools': schools, 'network_totals': network_totals})

    except Exception as e:
        logger.error(f"Error fetching suspensions summary: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/suspensions/grades', methods=['GET'])
@login_required
def suspensions_grades():
    """Grade breakdown for one school (drill-down level 1)."""
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    access = get_suspensions_access(user_email)

    if not access:
        return jsonify({'error': 'Access denied.'}), 403

    school = request.args.get('school', '')
    if not school:
        return jsonify({'error': 'School is required.'}), 400

    acl_conds, acl_params = _get_access_condition(access)

    suspension_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    conditions = acl_conds + ["School_Short_Name = @school"]
    params = list(acl_params) + [bigquery.ScalarQueryParameter("school", "STRING", school)]

    if date_from:
        conditions.append("CAST(Incident_Date AS DATE) >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "DATE", date_from))
    if date_to:
        conditions.append("CAST(Incident_Date AS DATE) <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "DATE", date_to))

    where_clause = " AND ".join(conditions)

    try:
        if suspension_type == 'iss':
            query = f"""
                SELECT
                    Grade_Level as grade,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}
                GROUP BY Grade_Level
            """
        elif suspension_type == 'oss':
            query = f"""
                SELECT
                    Grade_Level as grade,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}
                GROUP BY Grade_Level
            """
        else:
            query = f"""
                SELECT
                    Grade_Level as grade,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}
                GROUP BY Grade_Level

                UNION ALL

                SELECT
                    Grade_Level as grade,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}
                GROUP BY Grade_Level
            """

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = list(bq_client.query(query, job_config=job_config).result())

        # Aggregate by grade
        grade_data = {}
        for row in results:
            grade = row.grade
            if grade not in grade_data:
                grade_data[grade] = {
                    'grade': grade,
                    'iss_count': 0,
                    'oss_count': 0,
                    'iss_days': 0,
                    'oss_days': 0,
                }

            if row.type == 'ISS':
                grade_data[grade]['iss_count'] = row.incident_count or 0
                grade_data[grade]['iss_days'] = float(row.total_days or 0)
            else:
                grade_data[grade]['oss_count'] = row.incident_count or 0
                grade_data[grade]['oss_days'] = float(row.total_days or 0)

        grades = []
        for g, data in grade_data.items():
            data['total_incidents'] = data['iss_count'] + data['oss_count']
            data['total_days'] = data['iss_days'] + data['oss_days']
            grades.append(data)

        grades.sort(key=lambda x: x['grade'] if x['grade'] is not None else -1)

        logger.info(f"Suspensions grades: {len(grades)} grades for {school}")
        return jsonify({'grades': grades, 'school': school})

    except Exception as e:
        logger.error(f"Error fetching suspensions grades: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/suspensions/behaviors', methods=['GET'])
@login_required
def suspensions_behaviors():
    """Behavior breakdown for one school (alternative drill-down level 1)."""
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    access = get_suspensions_access(user_email)

    if not access:
        return jsonify({'error': 'Access denied.'}), 403

    school = request.args.get('school', '')
    if not school:
        return jsonify({'error': 'School is required.'}), 400

    acl_conds, acl_params = _get_access_condition(access)

    suspension_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    conditions = acl_conds + ["School_Short_Name = @school"]
    params = list(acl_params) + [bigquery.ScalarQueryParameter("school", "STRING", school)]

    if date_from:
        conditions.append("CAST(Incident_Date AS DATE) >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "DATE", date_from))
    if date_to:
        conditions.append("CAST(Incident_Date AS DATE) <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "DATE", date_to))

    where_clause = " AND ".join(conditions)

    try:
        if suspension_type == 'iss':
            query = f"""
                SELECT
                    COALESCE(Behavior, 'Unknown') as behavior,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}
                GROUP BY Behavior
            """
        elif suspension_type == 'oss':
            query = f"""
                SELECT
                    COALESCE(Behavior, 'Unknown') as behavior,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}
                GROUP BY Behavior
            """
        else:
            query = f"""
                SELECT
                    COALESCE(Behavior, 'Unknown') as behavior,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}
                GROUP BY Behavior

                UNION ALL

                SELECT
                    COALESCE(Behavior, 'Unknown') as behavior,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    COUNT(DISTINCT Student_Number) as students_affected
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}
                GROUP BY Behavior
            """

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = list(bq_client.query(query, job_config=job_config).result())

        # Aggregate by behavior
        behavior_data = {}
        for row in results:
            behavior = row.behavior
            if behavior not in behavior_data:
                behavior_data[behavior] = {
                    'behavior': behavior,
                    'iss_count': 0,
                    'oss_count': 0,
                    'iss_days': 0,
                    'oss_days': 0,
                }

            if row.type == 'ISS':
                behavior_data[behavior]['iss_count'] = row.incident_count or 0
                behavior_data[behavior]['iss_days'] = float(row.total_days or 0)
            else:
                behavior_data[behavior]['oss_count'] = row.incident_count or 0
                behavior_data[behavior]['oss_days'] = float(row.total_days or 0)

        behaviors = []
        for b, data in behavior_data.items():
            data['total_incidents'] = data['iss_count'] + data['oss_count']
            data['total_days'] = data['iss_days'] + data['oss_days']
            behaviors.append(data)

        behaviors.sort(key=lambda x: x['total_incidents'], reverse=True)

        logger.info(f"Suspensions behaviors: {len(behaviors)} behaviors for {school}")
        return jsonify({'behaviors': behaviors, 'school': school})

    except Exception as e:
        logger.error(f"Error fetching suspensions behaviors: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/suspensions/students', methods=['GET'])
@login_required
def suspensions_students():
    """Student list for one school (drill-down level 2)."""
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    access = get_suspensions_access(user_email)

    if not access:
        return jsonify({'error': 'Access denied.'}), 403

    school = request.args.get('school', '')
    if not school:
        return jsonify({'error': 'School is required.'}), 400

    acl_conds, acl_params = _get_access_condition(access)

    grade = request.args.get('grade', '')
    suspension_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    conditions = acl_conds + ["School_Short_Name = @school"]
    params = list(acl_params) + [bigquery.ScalarQueryParameter("school", "STRING", school)]

    if grade:
        conditions.append("Grade_Level = @grade")
        params.append(bigquery.ScalarQueryParameter("grade", "INT64", int(grade)))
    if date_from:
        conditions.append("CAST(Incident_Date AS DATE) >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "DATE", date_from))
    if date_to:
        conditions.append("CAST(Incident_Date AS DATE) <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "DATE", date_to))

    where_clause = " AND ".join(conditions)

    try:
        if suspension_type == 'iss':
            query = f"""
                SELECT
                    Student_Number as student_number,
                    LastFirst as name,
                    Grade_Level as grade,
                    Home_Room as home_room,
                    'ISS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    MAX(Incident_Date) as last_incident
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}
                GROUP BY Student_Number, LastFirst, Grade_Level, Home_Room
            """
        elif suspension_type == 'oss':
            query = f"""
                SELECT
                    Student_Number as student_number,
                    LastFirst as name,
                    Grade_Level as grade,
                    Home_Room as home_room,
                    'OSS' as type,
                    COUNT(*) as incident_count,
                    COALESCE(SUM(Days), 0) as total_days,
                    MAX(Incident_Date) as last_incident
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}
                GROUP BY Student_Number, LastFirst, Grade_Level, Home_Room
            """
        else:
            query = f"""
                WITH combined AS (
                    SELECT
                        Student_Number,
                        LastFirst,
                        Grade_Level,
                        Home_Room,
                        'ISS' as type,
                        Days,
                        Incident_Date
                    FROM `{SUSPENSIONS_ISS_TABLE}`
                    WHERE {where_clause}

                    UNION ALL

                    SELECT
                        Student_Number,
                        LastFirst,
                        Grade_Level,
                        Home_Room,
                        'OSS' as type,
                        Days,
                        Incident_Date
                    FROM `{SUSPENSIONS_OSS_TABLE}`
                    WHERE {where_clause}
                )
                SELECT
                    Student_Number as student_number,
                    LastFirst as name,
                    Grade_Level as grade,
                    Home_Room as home_room,
                    COUNTIF(type = 'ISS') as iss_count,
                    COUNTIF(type = 'OSS') as oss_count,
                    COALESCE(SUM(CASE WHEN type = 'ISS' THEN Days ELSE 0 END), 0) as iss_days,
                    COALESCE(SUM(CASE WHEN type = 'OSS' THEN Days ELSE 0 END), 0) as oss_days,
                    MAX(Incident_Date) as last_incident
                FROM combined
                GROUP BY Student_Number, LastFirst, Grade_Level, Home_Room
                ORDER BY (COUNTIF(type = 'ISS') + COUNTIF(type = 'OSS')) DESC
            """

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = list(bq_client.query(query, job_config=job_config).result())

        students = []
        for row in results:
            if suspension_type in ('iss', 'oss'):
                student_data = {
                    'student_number': str(row.student_number),
                    'name': row.name,
                    'grade': row.grade,
                    'home_room': row.home_room,
                    'iss_count': row.incident_count if suspension_type == 'iss' else 0,
                    'oss_count': row.incident_count if suspension_type == 'oss' else 0,
                    'iss_days': float(row.total_days) if suspension_type == 'iss' else 0,
                    'oss_days': float(row.total_days) if suspension_type == 'oss' else 0,
                    'total_incidents': row.incident_count,
                    'total_days': float(row.total_days),
                    'last_incident': row.last_incident.isoformat() if row.last_incident else None,
                }
            else:
                student_data = {
                    'student_number': str(row.student_number),
                    'name': row.name,
                    'grade': row.grade,
                    'home_room': row.home_room,
                    'iss_count': row.iss_count or 0,
                    'oss_count': row.oss_count or 0,
                    'iss_days': float(row.iss_days or 0),
                    'oss_days': float(row.oss_days or 0),
                    'total_incidents': (row.iss_count or 0) + (row.oss_count or 0),
                    'total_days': float(row.iss_days or 0) + float(row.oss_days or 0),
                    'last_incident': row.last_incident.isoformat() if row.last_incident else None,
                }
            students.append(student_data)

        logger.info(f"Suspensions students: {len(students)} students for {school}")
        return jsonify({'students': students, 'school': school})

    except Exception as e:
        logger.error(f"Error fetching suspensions students: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/suspensions/incidents', methods=['GET'])
@login_required
def suspensions_incidents():
    """Individual incidents for one student (drill-down level 3)."""
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    access = get_suspensions_access(user_email)

    if not access:
        return jsonify({'error': 'Access denied.'}), 403

    student_number = request.args.get('student_number', '')
    if not student_number:
        return jsonify({'error': 'student_number is required.'}), 400

    acl_conds, acl_params = _get_access_condition(access)

    suspension_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    conditions = acl_conds + ["Student_Number = @student_number"]
    params = list(acl_params) + [bigquery.ScalarQueryParameter("student_number", "STRING", student_number)]

    if date_from:
        conditions.append("CAST(Incident_Date AS DATE) >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "DATE", date_from))
    if date_to:
        conditions.append("CAST(Incident_Date AS DATE) <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "DATE", date_to))

    where_clause = " AND ".join(conditions)

    try:
        if suspension_type == 'iss':
            query = f"""
                SELECT
                    Incident_Date as date,
                    'ISS' as type,
                    Title as title,
                    Behavior as behavior,
                    Sub_Category as sub_category,
                    Days as days,
                    Incident_Creator as creator,
                    Action as action,
                    LastFirst as student_name,
                    School_Short_Name as school,
                    Grade_Level as grade
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}
                ORDER BY Incident_Date DESC
            """
        elif suspension_type == 'oss':
            query = f"""
                SELECT
                    Incident_Date as date,
                    'OSS' as type,
                    Title as title,
                    Behavior as behavior,
                    Sub_Category as sub_category,
                    Days as days,
                    Incident_Creator as creator,
                    Action as action,
                    LastFirst as student_name,
                    School_Short_Name as school,
                    Grade_Level as grade
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}
                ORDER BY Incident_Date DESC
            """
        else:
            query = f"""
                SELECT
                    Incident_Date as date,
                    'ISS' as type,
                    Title as title,
                    Behavior as behavior,
                    Sub_Category as sub_category,
                    Days as days,
                    Incident_Creator as creator,
                    Action as action,
                    LastFirst as student_name,
                    School_Short_Name as school,
                    Grade_Level as grade
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {where_clause}

                UNION ALL

                SELECT
                    Incident_Date as date,
                    'OSS' as type,
                    Title as title,
                    Behavior as behavior,
                    Sub_Category as sub_category,
                    Days as days,
                    Incident_Creator as creator,
                    Action as action,
                    LastFirst as student_name,
                    School_Short_Name as school,
                    Grade_Level as grade
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {where_clause}

                ORDER BY date DESC
            """

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = list(bq_client.query(query, job_config=job_config).result())

        incidents = []
        student_name = ''
        student_school = ''
        student_grade = ''

        for row in results:
            if not student_name and row.student_name:
                student_name = row.student_name
                student_school = row.school
                student_grade = row.grade

            incidents.append({
                'date': row.date.isoformat() if row.date else None,
                'type': row.type,
                'title': row.title,
                'behavior': row.behavior,
                'sub_category': row.sub_category,
                'days': float(row.days) if row.days else 0,
                'creator': row.creator,
                'action': row.action,
            })

        logger.info(f"Suspensions incidents: {len(incidents)} for student {student_number}")
        return jsonify({
            'incidents': incidents,
            'student_name': student_name,
            'student_school': student_school,
            'student_grade': student_grade
        })

    except Exception as e:
        logger.error(f"Error fetching suspensions incidents: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/api/suspensions/filter-options', methods=['GET'])
@login_required
def suspensions_filter_options():
    """Populate filter dropdowns for the Suspensions dashboard."""
    if not bq_client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    user = session.get('user', {})
    user_email = user.get('email', '').lower()
    access = get_suspensions_access(user_email)

    if not access:
        return jsonify({'error': 'Access denied.'}), 403

    acl_conds, acl_params = _get_access_condition(access)
    acl_where = " AND ".join(acl_conds) if acl_conds else "1=1"

    try:
        query = f"""
            WITH iss_data AS (
                SELECT School_Short_Name, Grade_Level, Behavior
                FROM `{SUSPENSIONS_ISS_TABLE}`
                WHERE {acl_where}
            ),
            oss_data AS (
                SELECT School_Short_Name, Grade_Level, Behavior
                FROM `{SUSPENSIONS_OSS_TABLE}`
                WHERE {acl_where}
            ),
            combined AS (
                SELECT * FROM iss_data
                UNION ALL
                SELECT * FROM oss_data
            )
            SELECT 'school' as option_type, School_Short_Name as value
            FROM combined
            GROUP BY School_Short_Name
            UNION ALL
            SELECT 'grade' as option_type, CAST(Grade_Level AS STRING) as value
            FROM combined
            WHERE Grade_Level IS NOT NULL
            GROUP BY Grade_Level
            UNION ALL
            SELECT 'behavior' as option_type, Behavior as value
            FROM combined
            WHERE Behavior IS NOT NULL
            GROUP BY Behavior
            ORDER BY option_type, value
        """

        job_config = bigquery.QueryJobConfig(query_parameters=acl_params)
        results = list(bq_client.query(query, job_config=job_config).result())

        options = {'schools': [], 'grades': [], 'behaviors': []}
        for row in results:
            if row.value:
                if row.option_type == 'school':
                    options['schools'].append(row.value)
                elif row.option_type == 'grade':
                    options['grades'].append(row.value)
                elif row.option_type == 'behavior':
                    options['behaviors'].append(row.value)

        logger.info(f"Suspensions filter options: {len(options['schools'])} schools, {len(options['grades'])} grades")
        return jsonify(options)

    except Exception as e:
        logger.error(f"Error fetching suspensions filter options: {e}")
        return jsonify({'error': str(e)}), 500
