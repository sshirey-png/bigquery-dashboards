"""
Salary Projection Dashboard Blueprint
Interactive salary scenario modeling for CEO presentations
"""

from flask import Blueprint, request, jsonify, send_from_directory, session
from functools import wraps
from google.cloud import bigquery
import os

bp = Blueprint('salary', __name__)
client = bigquery.Client()

# Import config
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROJECT_ID
from auth import login_required, get_salary_access


def salary_access_required(f):
    """Decorator to protect salary routes - requires C-Team access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        email = session.get('user', {}).get('email', '')
        access = get_salary_access(email)

        if not access or not access.get('has_access'):
            return jsonify({'error': 'Access denied. This dashboard is restricted to C-Team.'}), 403

        return f(*args, **kwargs)
    return decorated_function

HTML_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STAFF_TABLE = f'{PROJECT_ID}.talent_grow_observations.staff_master_list_with_function'
SALARY_SCHEDULE_TABLE = f'{PROJECT_ID}.Salary.salary_schedule'


@bp.route('/salary-dashboard')
def serve_dashboard():
    """Serve the salary dashboard HTML."""
    return send_from_directory(HTML_DIR, 'salary-dashboard.html')


@bp.route('/api/salary/access')
def check_salary_access():
    """Check if user has access to salary dashboard."""
    if 'user' not in session:
        return jsonify({'has_access': False, 'reason': 'Not authenticated'})

    email = session.get('user', {}).get('email', '')
    access = get_salary_access(email)

    if access and access.get('has_access'):
        return jsonify({
            'has_access': True,
            'access_type': access.get('access_type'),
            'label': access.get('label')
        })

    return jsonify({
        'has_access': False,
        'reason': 'This dashboard is restricted to C-Team (Chief and Ex. Dir titles only).'
    })


@bp.route('/api/salary/summary')
@salary_access_required
def get_salary_summary():
    """
    Get salary projections with configurable parameters.

    Query params:
    - step_cap: Maximum step to use (default 30)
    - scenario: 'base', 'option1', 'option2', or 'all' (default 'all')
    - school: Filter by school (optional)
    """
    step_cap = int(request.args.get('step_cap', 30))
    school = request.args.get('school', '')

    school_filter = ""
    if school:
        school_filter = f'AND Location_Name = "{school}"'

    query = f"""
    WITH
    staff AS (
      SELECT
        Employee_Number,
        Employee_Name__Last_Suffix__First_MI_ as name,
        Job_Title,
        Location_Name as school,
        Relevant_Years_of_Experience as current_yoe,
        -- For schedule lookup: cap at 30 (schedule max)
        LEAST(COALESCE(Relevant_Years_of_Experience, 0), 30) as current_step,
        LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, 30) as next_year_step_schedule,
        -- For Option 1 / Custom: use user-selected cap
        LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, {step_cap}) as next_year_step_capped,
        CASE
          WHEN LOWER(Job_Title) LIKE "%paraprofessional%" THEN "Paraprofessional"
          WHEN LOWER(Job_Title) LIKE "%asst teacher%" OR LOWER(Job_Title) LIKE "%assistant teacher%" THEN "Asst_Teacher"
          WHEN LOWER(Job_Title) LIKE "%teacher%" THEN "Teacher"
          ELSE NULL
        END as salary_category
      FROM `{STAFF_TABLE}`
      WHERE Employment_Status IN ("Active", "Leave of absence")
      {school_filter}
    ),
    projections AS (
      SELECT
        s.*,
        -- Current salary (schedule max at 30)
        CASE s.salary_category
          WHEN "Paraprofessional" THEN curr.paraprofessional
          WHEN "Asst_Teacher" THEN curr.asst_teacher
          WHEN "Teacher" THEN curr.teacher
        END as current_salary,
        -- Next year base (schedule max at 30)
        CASE s.salary_category
          WHEN "Paraprofessional" THEN next_schedule.paraprofessional
          WHEN "Asst_Teacher" THEN next_schedule.asst_teacher
          WHEN "Teacher" THEN next_schedule.teacher
        END as next_base,
        -- Option 1 (user-selected cap)
        CASE s.salary_category
          WHEN "Paraprofessional" THEN next_capped.paraprofessional_option
          WHEN "Asst_Teacher" THEN next_capped.asst_teacher_option
          WHEN "Teacher" THEN next_capped.teacher_option_1
        END as next_opt1,
        -- Option 2 (Teacher only, user-selected cap)
        CASE s.salary_category
          WHEN "Teacher" THEN next_capped.teacher_option_2
          ELSE NULL
        END as next_opt2
      FROM staff s
      LEFT JOIN `{SALARY_SCHEDULE_TABLE}` curr
        ON curr.step = s.current_step
      LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next_schedule
        ON next_schedule.step = s.next_year_step_schedule
      LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next_capped
        ON next_capped.step = s.next_year_step_capped
      WHERE s.salary_category IS NOT NULL
    )
    SELECT
      salary_category,
      COUNT(*) as employee_count,
      ROUND(SUM(current_salary), 0) as current_total,
      ROUND(SUM(next_base), 0) as next_base_total,
      ROUND(SUM(next_opt1), 0) as next_opt1_total,
      ROUND(SUM(next_opt2), 0) as next_opt2_total,
      ROUND(AVG(current_yoe), 1) as avg_yoe,
      SUM(CASE WHEN current_yoe > 20 THEN 1 ELSE 0 END) as above_20_years,
      SUM(CASE WHEN current_yoe > 15 THEN 1 ELSE 0 END) as above_15_years,
      SUM(CASE WHEN current_yoe > 10 THEN 1 ELSE 0 END) as above_10_years
    FROM projections
    GROUP BY salary_category
    ORDER BY salary_category
    """

    results = client.query(query).result()

    categories = []
    totals = {
        'employee_count': 0,
        'current_total': 0,
        'next_base_total': 0,
        'next_opt1_total': 0,
        'next_opt2_total': 0,
        'above_20_years': 0,
        'above_15_years': 0,
        'above_10_years': 0
    }

    for row in results:
        cat = {
            'category': row.salary_category,
            'employee_count': row.employee_count,
            'current_total': row.current_total or 0,
            'next_base_total': row.next_base_total or 0,
            'next_opt1_total': row.next_opt1_total or 0,
            'next_opt2_total': row.next_opt2_total or 0,
            'avg_yoe': row.avg_yoe or 0,
            'above_20_years': row.above_20_years or 0,
            'above_15_years': row.above_15_years or 0,
            'above_10_years': row.above_10_years or 0
        }
        categories.append(cat)

        for key in totals:
            totals[key] += cat.get(key, 0)

    return jsonify({
        'step_cap': step_cap,
        'categories': categories,
        'totals': totals
    })


@bp.route('/api/salary/distribution')
@salary_access_required
def get_yoe_distribution():
    """Get distribution of years of experience."""
    school = request.args.get('school', '')
    category = request.args.get('category', '')

    conditions = ['Employment_Status IN ("Active", "Leave of absence")']
    if school:
        conditions.append(f'Location_Name = "{school}"')

    category_case = """
    CASE
      WHEN LOWER(Job_Title) LIKE "%paraprofessional%" THEN "Paraprofessional"
      WHEN LOWER(Job_Title) LIKE "%asst teacher%" OR LOWER(Job_Title) LIKE "%assistant teacher%" THEN "Asst_Teacher"
      WHEN LOWER(Job_Title) LIKE "%teacher%" THEN "Teacher"
      ELSE NULL
    END
    """

    if category:
        conditions.append(f'({category_case}) = "{category}"')
    else:
        conditions.append(f'({category_case}) IS NOT NULL')

    where_clause = ' AND '.join(conditions)

    query = f"""
    SELECT
      COALESCE(Relevant_Years_of_Experience, 0) as yoe,
      COUNT(*) as count
    FROM `{STAFF_TABLE}`
    WHERE {where_clause}
    GROUP BY yoe
    ORDER BY yoe
    """

    results = client.query(query).result()

    distribution = [{'yoe': row.yoe, 'count': row.count} for row in results]

    return jsonify({'distribution': distribution})


@bp.route('/api/salary/employees')
@salary_access_required
def get_employees():
    """Get employee list with salary details, including custom scenario if provided."""
    step_cap = int(request.args.get('step_cap', 30))
    school = request.args.get('school', '')
    category = request.args.get('category', '')
    min_yoe = request.args.get('min_yoe', '')
    max_yoe = request.args.get('max_yoe', '')

    # Custom scenario parameters
    custom_mode = request.args.get('custom_mode', 'false').lower() == 'true'
    para_schedule = request.args.get('para_schedule', 'false').lower() == 'true'
    asst_schedule = request.args.get('asst_schedule', 'false').lower() == 'true'
    teacher_schedule = request.args.get('teacher_schedule', 'false').lower() == 'true'
    base_para = request.args.get('base_para', '')
    base_asst = request.args.get('base_asst', '')
    base_teacher = request.args.get('base_teacher', '')
    annual_increase = float(request.args.get('annual_increase', 0))
    teacher_hybrid = request.args.get('teacher_hybrid', 'false').lower() == 'true' and not teacher_schedule
    hybrid_threshold = int(request.args.get('hybrid_threshold', 10))
    hybrid_rate_1 = float(request.args.get('hybrid_rate_1', 2.0))
    hybrid_rate_2 = float(request.args.get('hybrid_rate_2', 1.5))

    conditions = ['Employment_Status IN ("Active", "Leave of absence")']
    if school:
        conditions.append(f'Location_Name = "{school}"')

    where_clause = ' AND '.join(conditions)

    # Build custom salary formulas if in custom mode
    if custom_mode and (annual_increase > 0 or teacher_hybrid):
        base_para = float(base_para) if base_para else 28850
        base_asst = float(base_asst) if base_asst else 31900
        base_teacher = float(base_teacher) if base_teacher else 48000
        rate = 1 + (annual_increase / 100) if annual_increase > 0 else 1.02
        rate1 = 1 + (hybrid_rate_1 / 100)
        rate2 = 1 + (hybrid_rate_2 / 100)

        # Para formula
        if para_schedule:
            para_next_formula = "next.paraprofessional"
        else:
            para_next_formula = f"{base_para} * POWER({rate}, s.next_year_step)"

        # Asst formula
        if asst_schedule:
            asst_next_formula = "next.asst_teacher"
        else:
            asst_next_formula = f"{base_asst} * POWER({rate}, s.next_year_step)"

        # Teacher formula
        if teacher_schedule:
            teacher_next_formula = "next.teacher"
        elif teacher_hybrid:
            teacher_next_formula = f"""
              CASE
                WHEN s.next_year_step <= {hybrid_threshold} THEN {base_teacher} * POWER({rate1}, s.next_year_step)
                ELSE {base_teacher} * POWER({rate1}, {hybrid_threshold}) * POWER({rate2}, s.next_year_step - {hybrid_threshold})
              END
            """
        else:
            teacher_next_formula = f"{base_teacher} * POWER({rate}, s.next_year_step)"

        custom_salary_select = f"""
            CASE s.salary_category
              WHEN "Paraprofessional" THEN {para_next_formula}
              WHEN "Asst_Teacher" THEN {asst_next_formula}
              WHEN "Teacher" THEN {teacher_next_formula}
            END as next_custom,
        """
    else:
        custom_salary_select = "NULL as next_custom,"

    query = f"""
    WITH
    staff AS (
      SELECT
        Employee_Number,
        Employee_Name__Last_Suffix__First_MI_ as name,
        Job_Title,
        Location_Name as school,
        Relevant_Years_of_Experience as current_yoe,
        -- For schedule lookup: cap at 30 (schedule max)
        LEAST(COALESCE(Relevant_Years_of_Experience, 0), 30) as current_step,
        LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, 30) as next_year_step_schedule,
        -- For Option 1 / Custom: use user-selected cap
        LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, {step_cap}) as next_year_step,
        CASE
          WHEN LOWER(Job_Title) LIKE "%paraprofessional%" THEN "Paraprofessional"
          WHEN LOWER(Job_Title) LIKE "%asst teacher%" OR LOWER(Job_Title) LIKE "%assistant teacher%" THEN "Asst_Teacher"
          WHEN LOWER(Job_Title) LIKE "%teacher%" THEN "Teacher"
          ELSE NULL
        END as salary_category
      FROM `{STAFF_TABLE}`
      WHERE {where_clause}
    ),
    projections AS (
      SELECT
        s.*,
        CASE s.salary_category
          WHEN "Paraprofessional" THEN curr.paraprofessional
          WHEN "Asst_Teacher" THEN curr.asst_teacher
          WHEN "Teacher" THEN curr.teacher
        END as current_salary,
        CASE s.salary_category
          WHEN "Paraprofessional" THEN next_schedule.paraprofessional
          WHEN "Asst_Teacher" THEN next_schedule.asst_teacher
          WHEN "Teacher" THEN next_schedule.teacher
        END as next_base,
        CASE s.salary_category
          WHEN "Paraprofessional" THEN next_capped.paraprofessional_option
          WHEN "Asst_Teacher" THEN next_capped.asst_teacher_option
          WHEN "Teacher" THEN next_capped.teacher_option_1
        END as next_opt1,
        {custom_salary_select}
        CASE s.salary_category
          WHEN "Teacher" THEN next_capped.teacher_option_2
          ELSE NULL
        END as next_opt2
      FROM staff s
      LEFT JOIN `{SALARY_SCHEDULE_TABLE}` curr
        ON curr.step = s.current_step
      LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next_schedule
        ON next_schedule.step = s.next_year_step_schedule
      LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next_capped
        ON next_capped.step = s.next_year_step
      WHERE s.salary_category IS NOT NULL
    )
    SELECT *
    FROM projections
    WHERE 1=1
    {"AND salary_category = '" + category + "'" if category else ""}
    {"AND current_yoe >= " + min_yoe if min_yoe else ""}
    {"AND current_yoe <= " + max_yoe if max_yoe else ""}
    ORDER BY salary_category, current_yoe DESC, name
    """

    results = client.query(query).result()

    employees = []
    for row in results:
        emp = {
            'employee_number': row.Employee_Number,
            'name': row.name,
            'job_title': row.Job_Title,
            'school': row.school,
            'category': row.salary_category,
            'current_yoe': row.current_yoe or 0,
            'next_step': row.next_year_step,
            'current_salary': row.current_salary or 0,
            'next_base': row.next_base or 0,
            'next_opt1': row.next_opt1 or 0,
            'next_opt2': row.next_opt2
        }
        if custom_mode:
            emp['next_custom'] = row.next_custom or 0
        employees.append(emp)

    return jsonify({'employees': employees, 'custom_mode': custom_mode})


@bp.route('/api/salary/schools')
@salary_access_required
def get_schools():
    """Get list of schools for filter dropdown."""
    query = f"""
    SELECT DISTINCT Location_Name as school
    FROM `{STAFF_TABLE}`
    WHERE Employment_Status IN ("Active", "Leave of absence")
      AND Location_Name IS NOT NULL
    ORDER BY school
    """

    results = client.query(query).result()
    schools = [row.school for row in results]

    return jsonify({'schools': schools})


@bp.route('/api/salary/schedule')
@salary_access_required
def get_salary_schedule():
    """Get the full salary schedule for reference."""
    query = f"""
    SELECT *
    FROM `{SALARY_SCHEDULE_TABLE}`
    ORDER BY step
    """

    results = client.query(query).result()

    schedule = []
    for row in results:
        schedule.append({
            'step': row.step,
            'paraprofessional': row.paraprofessional,
            'paraprofessional_option': row.paraprofessional_option,
            'asst_teacher': row.asst_teacher,
            'asst_teacher_option': row.asst_teacher_option,
            'teacher': row.teacher,
            'teacher_option_1': row.teacher_option_1,
            'teacher_option_2': row.teacher_option_2
        })

    return jsonify({'schedule': schedule})


@bp.route('/api/salary/compare-caps')
@salary_access_required
def compare_step_caps():
    """Compare different step cap scenarios side by side."""
    caps = request.args.get('caps', '15,20,25,30').split(',')
    school = request.args.get('school', '')

    school_filter = ""
    if school:
        school_filter = f'AND Location_Name = "{school}"'

    results = []

    for cap in caps:
        cap = int(cap.strip())

        query = f"""
        WITH
        staff AS (
          SELECT
            Employee_Number,
            Job_Title,
            Relevant_Years_of_Experience as current_yoe,
            -- For schedule lookup: cap at 30 (schedule max)
            LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, 30) as next_year_step_schedule,
            -- For Option 1: use comparison cap
            LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, {cap}) as next_year_step_capped,
            CASE
              WHEN LOWER(Job_Title) LIKE "%paraprofessional%" THEN "Paraprofessional"
              WHEN LOWER(Job_Title) LIKE "%asst teacher%" OR LOWER(Job_Title) LIKE "%assistant teacher%" THEN "Asst_Teacher"
              WHEN LOWER(Job_Title) LIKE "%teacher%" THEN "Teacher"
              ELSE NULL
            END as salary_category
          FROM `{STAFF_TABLE}`
          WHERE Employment_Status IN ("Active", "Leave of absence")
          {school_filter}
        ),
        projections AS (
          SELECT
            s.*,
            -- Base uses schedule (max at 30)
            CASE s.salary_category
              WHEN "Paraprofessional" THEN next_schedule.paraprofessional
              WHEN "Asst_Teacher" THEN next_schedule.asst_teacher
              WHEN "Teacher" THEN next_schedule.teacher
            END as next_base,
            -- Option 1 uses comparison cap
            CASE s.salary_category
              WHEN "Paraprofessional" THEN next_capped.paraprofessional_option
              WHEN "Asst_Teacher" THEN next_capped.asst_teacher_option
              WHEN "Teacher" THEN next_capped.teacher_option_1
            END as next_opt1,
            CASE s.salary_category
              WHEN "Teacher" THEN next_capped.teacher_option_2
              ELSE NULL
            END as next_opt2
          FROM staff s
          LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next_schedule
            ON next_schedule.step = s.next_year_step_schedule
          LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next_capped
            ON next_capped.step = s.next_year_step_capped
          WHERE s.salary_category IS NOT NULL
        )
        SELECT
          COUNT(*) as employee_count,
          ROUND(SUM(next_base), 0) as base_total,
          ROUND(SUM(next_opt1), 0) as opt1_total,
          SUM(CASE WHEN current_yoe > {cap} THEN 1 ELSE 0 END) as capped_count
        FROM projections
        """

        row = list(client.query(query).result())[0]

        results.append({
            'step_cap': cap,
            'employee_count': row.employee_count,
            'base_total': row.base_total or 0,
            'opt1_total': row.opt1_total or 0,
            'capped_count': row.capped_count or 0
        })

    return jsonify({'comparisons': results})


@bp.route('/api/salary/custom-scenario')
@salary_access_required
def custom_scenario():
    """
    Model custom salary scenarios with adjustable parameters.

    Query params:
    - step_cap: Maximum step (default 30)
    - base_para: Base salary for paraprofessional at step 0 (default from schedule)
    - base_asst: Base salary for asst teacher at step 0 (default from schedule)
    - base_teacher: Base salary for teacher at step 0 (default from schedule)
    - para_schedule: If 'true', use schedule for paras instead of custom
    - asst_schedule: If 'true', use schedule for asst teachers instead of custom
    - teacher_schedule: If 'true', use schedule for teachers instead of custom
    - annual_increase: Annual step increase percentage (default 1.0 = current schedule)
    - teacher_hybrid: If 'true', use hybrid rate for teachers (2% first 10 yrs, 1.5% after)
    - hybrid_threshold: Year when hybrid switches (default 10)
    - hybrid_rate_1: First rate percentage (default 2.0)
    - hybrid_rate_2: Second rate percentage (default 1.5)
    - school: Filter by school (optional)
    """
    step_cap = int(request.args.get('step_cap', 30))
    school = request.args.get('school', '')

    # Per-category schedule toggles
    para_schedule = request.args.get('para_schedule', 'false').lower() == 'true'
    asst_schedule = request.args.get('asst_schedule', 'false').lower() == 'true'
    teacher_schedule = request.args.get('teacher_schedule', 'false').lower() == 'true'

    # Custom scenario parameters
    base_para = request.args.get('base_para', '')
    base_asst = request.args.get('base_asst', '')
    base_teacher = request.args.get('base_teacher', '')
    annual_increase = float(request.args.get('annual_increase', 0))  # 0 means use schedule

    # Hybrid parameters for teachers
    teacher_hybrid = request.args.get('teacher_hybrid', 'false').lower() == 'true' and not teacher_schedule
    hybrid_threshold = int(request.args.get('hybrid_threshold', 10))
    hybrid_rate_1 = float(request.args.get('hybrid_rate_1', 2.0))
    hybrid_rate_2 = float(request.args.get('hybrid_rate_2', 1.5))

    school_filter = ""
    if school:
        school_filter = f'AND Location_Name = "{school}"'

    # Check if any category needs custom calculation
    any_custom = (not para_schedule or not asst_schedule or not teacher_schedule) and annual_increase > 0

    # If custom bases provided, calculate dynamically
    if any_custom or teacher_hybrid:
        # Use defaults from step 0 if not provided
        base_para = float(base_para) if base_para else 28850
        base_asst = float(base_asst) if base_asst else 31900
        base_teacher = float(base_teacher) if base_teacher else 48000

        rate = 1 + (annual_increase / 100) if annual_increase > 0 else 1.02  # default 2%
        rate1 = 1 + (hybrid_rate_1 / 100)
        rate2 = 1 + (hybrid_rate_2 / 100)

        # Build para salary formula - use schedule or custom
        if para_schedule:
            para_current_formula = "curr.paraprofessional"
            para_next_formula = "next.paraprofessional"
        else:
            para_current_formula = f"{base_para} * POWER({rate}, s.capped_yoe)"
            para_next_formula = f"{base_para} * POWER({rate}, s.next_year_step)"

        # Build asst teacher salary formula - use schedule or custom
        if asst_schedule:
            asst_current_formula = "curr.asst_teacher"
            asst_next_formula = "next.asst_teacher"
        else:
            asst_current_formula = f"{base_asst} * POWER({rate}, s.capped_yoe)"
            asst_next_formula = f"{base_asst} * POWER({rate}, s.next_year_step)"

        # Build teacher salary formula based on hybrid mode or schedule
        if teacher_schedule:
            teacher_current_formula = "curr.teacher"
            teacher_next_formula = "next.teacher"
        elif teacher_hybrid:
            # Hybrid: 2% for first N years, then 1.5%
            # Formula: IF step <= threshold: base * rate1^step
            #          ELSE: base * rate1^threshold * rate2^(step - threshold)
            teacher_current_formula = f"""
              CASE
                WHEN s.capped_yoe <= {hybrid_threshold} THEN {base_teacher} * POWER({rate1}, s.capped_yoe)
                ELSE {base_teacher} * POWER({rate1}, {hybrid_threshold}) * POWER({rate2}, s.capped_yoe - {hybrid_threshold})
              END
            """
            teacher_next_formula = f"""
              CASE
                WHEN s.next_year_step <= {hybrid_threshold} THEN {base_teacher} * POWER({rate1}, s.next_year_step)
                ELSE {base_teacher} * POWER({rate1}, {hybrid_threshold}) * POWER({rate2}, s.next_year_step - {hybrid_threshold})
              END
            """
        else:
            # Flat rate
            teacher_current_formula = f"{base_teacher} * POWER({rate}, s.capped_yoe)"
            teacher_next_formula = f"{base_teacher} * POWER({rate}, s.next_year_step)"

        query = f"""
        WITH
        staff AS (
          SELECT
            Employee_Number,
            Job_Title,
            Location_Name as school,
            Relevant_Years_of_Experience as current_yoe,
            LEAST(COALESCE(Relevant_Years_of_Experience, 0), {step_cap}) as capped_yoe,
            LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, {step_cap}) as next_year_step,
            CASE
              WHEN LOWER(Job_Title) LIKE "%paraprofessional%" THEN "Paraprofessional"
              WHEN LOWER(Job_Title) LIKE "%asst teacher%" OR LOWER(Job_Title) LIKE "%assistant teacher%" THEN "Asst_Teacher"
              WHEN LOWER(Job_Title) LIKE "%teacher%" THEN "Teacher"
              ELSE NULL
            END as salary_category
          FROM `{STAFF_TABLE}`
          WHERE Employment_Status IN ("Active", "Leave of absence")
          {school_filter}
        ),
        projections AS (
          SELECT
            s.*,
            -- Current custom salary (per-category: schedule or custom)
            CASE s.salary_category
              WHEN "Paraprofessional" THEN {para_current_formula}
              WHEN "Asst_Teacher" THEN {asst_current_formula}
              WHEN "Teacher" THEN {teacher_current_formula}
            END as current_custom,
            -- Next year custom salary (per-category: schedule or custom)
            CASE s.salary_category
              WHEN "Paraprofessional" THEN {para_next_formula}
              WHEN "Asst_Teacher" THEN {asst_next_formula}
              WHEN "Teacher" THEN {teacher_next_formula}
            END as next_custom,
            -- Current schedule salary for comparison
            CASE s.salary_category
              WHEN "Paraprofessional" THEN curr.paraprofessional
              WHEN "Asst_Teacher" THEN curr.asst_teacher
              WHEN "Teacher" THEN curr.teacher
            END as current_schedule,
            -- Next schedule salary for comparison
            CASE s.salary_category
              WHEN "Paraprofessional" THEN next.paraprofessional
              WHEN "Asst_Teacher" THEN next.asst_teacher
              WHEN "Teacher" THEN next.teacher
            END as next_schedule
          FROM staff s
          LEFT JOIN `{SALARY_SCHEDULE_TABLE}` curr
            ON curr.step = s.capped_yoe
          LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next
            ON next.step = s.next_year_step
          WHERE s.salary_category IS NOT NULL
        )
        SELECT
          salary_category,
          COUNT(*) as employee_count,
          ROUND(SUM(current_schedule), 0) as current_schedule_total,
          ROUND(SUM(next_schedule), 0) as next_schedule_total,
          ROUND(SUM(current_custom), 0) as current_custom_total,
          ROUND(SUM(next_custom), 0) as next_custom_total,
          ROUND(AVG(current_yoe), 1) as avg_yoe
        FROM projections
        GROUP BY salary_category
        ORDER BY salary_category
        """
    else:
        # Just return schedule-based results
        query = f"""
        WITH
        staff AS (
          SELECT
            Employee_Number,
            Job_Title,
            Location_Name as school,
            Relevant_Years_of_Experience as current_yoe,
            LEAST(COALESCE(Relevant_Years_of_Experience, 0), {step_cap}) as capped_yoe,
            LEAST(COALESCE(Relevant_Years_of_Experience, 0) + 1, {step_cap}) as next_year_step,
            CASE
              WHEN LOWER(Job_Title) LIKE "%paraprofessional%" THEN "Paraprofessional"
              WHEN LOWER(Job_Title) LIKE "%asst teacher%" OR LOWER(Job_Title) LIKE "%assistant teacher%" THEN "Asst_Teacher"
              WHEN LOWER(Job_Title) LIKE "%teacher%" THEN "Teacher"
              ELSE NULL
            END as salary_category
          FROM `{STAFF_TABLE}`
          WHERE Employment_Status IN ("Active", "Leave of absence")
          {school_filter}
        ),
        projections AS (
          SELECT
            s.*,
            CASE s.salary_category
              WHEN "Paraprofessional" THEN curr.paraprofessional
              WHEN "Asst_Teacher" THEN curr.asst_teacher
              WHEN "Teacher" THEN curr.teacher
            END as current_schedule,
            CASE s.salary_category
              WHEN "Paraprofessional" THEN next.paraprofessional
              WHEN "Asst_Teacher" THEN next.asst_teacher
              WHEN "Teacher" THEN next.teacher
            END as next_schedule
          FROM staff s
          LEFT JOIN `{SALARY_SCHEDULE_TABLE}` curr
            ON curr.step = s.capped_yoe
          LEFT JOIN `{SALARY_SCHEDULE_TABLE}` next
            ON next.step = s.next_year_step
          WHERE s.salary_category IS NOT NULL
        )
        SELECT
          salary_category,
          COUNT(*) as employee_count,
          ROUND(SUM(current_schedule), 0) as current_schedule_total,
          ROUND(SUM(next_schedule), 0) as next_schedule_total,
          ROUND(SUM(current_schedule), 0) as current_custom_total,
          ROUND(SUM(next_schedule), 0) as next_custom_total,
          ROUND(AVG(current_yoe), 1) as avg_yoe
        FROM projections
        GROUP BY salary_category
        ORDER BY salary_category
        """

    results = client.query(query).result()

    categories = []
    totals = {
        'employee_count': 0,
        'current_schedule_total': 0,
        'next_schedule_total': 0,
        'current_custom_total': 0,
        'next_custom_total': 0
    }

    for row in results:
        cat = {
            'category': row.salary_category,
            'employee_count': row.employee_count,
            'current_schedule_total': row.current_schedule_total or 0,
            'next_schedule_total': row.next_schedule_total or 0,
            'current_custom_total': row.current_custom_total or 0,
            'next_custom_total': row.next_custom_total or 0,
            'avg_yoe': row.avg_yoe or 0
        }
        categories.append(cat)

        for key in totals:
            totals[key] += cat.get(key, 0)

    return jsonify({
        'step_cap': step_cap,
        'base_para': base_para if base_para else 28850,
        'base_asst': base_asst if base_asst else 31900,
        'base_teacher': base_teacher if base_teacher else 48000,
        'annual_increase': annual_increase if annual_increase else 'schedule',
        'categories': categories,
        'totals': totals
    })
