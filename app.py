"""
Flask backend for Supervisor Dashboard
Provides API endpoints for BigQuery data access
With Google OAuth 2.0 authentication
"""

from flask import Flask, jsonify, send_from_directory, redirect, url_for, session, request
from flask_cors import CORS
from google.cloud import bigquery
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import logging
import os
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Fix for running behind Cloud Run proxy (ensures HTTPS redirect URIs)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Session configuration
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') != 'development'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CORS configuration - allow your domain in production
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# OAuth configuration
ALLOWED_DOMAIN = 'firstlineschools.org'
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Dev mode - bypasses OAuth for local testing
DEV_MODE = os.environ.get('FLASK_ENV') == 'development' or not GOOGLE_CLIENT_ID
DEV_USER_EMAIL = 'sshirey@firstlineschools.org'  # Default dev user

# Admin emails - these users have access to ALL supervisors
ADMIN_EMAILS = [
    'sshirey@firstlineschools.org',      # Scott Shirey - Chief People Officer
    'brichardson@firstlineschools.org',  # Brittney Richardson - Chief of Human Resources
    'spence@firstlineschools.org',       # Sabrina Pence
]

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# BigQuery configuration
PROJECT_ID = 'talent-demo-482004'
DATASET_ID = 'talent_grow_observations'
TABLE_ID = 'supervisor_dashboard_data'

# Initialize BigQuery client with application default credentials
try:
    client = bigquery.Client(project=PROJECT_ID)
    logger.info(f"BigQuery client initialized for project: {PROJECT_ID}")
except Exception as e:
    logger.error(f"Failed to initialize BigQuery client: {e}")
    client = None


# ============================================
# Authentication Helpers
# ============================================

def login_required(f):
    """Decorator to protect routes - requires valid session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_supervisor_name_for_email(email):
    """
    Look up supervisor name from BigQuery by email address.
    Returns the supervisor name if found, None otherwise.
    """
    if not client or not email:
        return None

    try:
        query = f"""
            SELECT DISTINCT Supervisor_Name__Unsecured_
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            WHERE LOWER(Supervisor_Email) = LOWER(@email)
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        if results:
            return results[0].Supervisor_Name__Unsecured_
        return None
    except Exception as e:
        logger.error(f"Error looking up supervisor for email {email}: {e}")
        return None


def is_admin(email):
    """Check if the user is an admin with full access."""
    return email.lower() in [e.lower() for e in ADMIN_EMAILS]


def get_all_supervisors():
    """Get list of all unique supervisor names from BigQuery."""
    if not client:
        return []

    try:
        query = f"""
            SELECT DISTINCT Supervisor_Name__Unsecured_
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
            WHERE Supervisor_Name__Unsecured_ IS NOT NULL
            ORDER BY Supervisor_Name__Unsecured_
        """
        query_job = client.query(query)
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
    if not client:
        return []

    # Admins get access to all supervisors
    if is_admin(email):
        logger.info(f"Admin user {email} - granting access to all supervisors")
        return get_all_supervisors()

    # If user is not a supervisor, they have no access
    if not supervisor_name:
        return []

    try:
        # Use recursive CTE to find all supervisors in the user's downline
        # This traverses the hierarchy: user -> their direct reports -> their reports' reports, etc.
        query = f"""
            WITH RECURSIVE
            -- Get all supervisors with their email (for mapping employee to supervisor name format)
            supervisor_lookup AS (
                SELECT DISTINCT
                    Supervisor_Name__Unsecured_ AS supervisor_name,
                    Supervisor_Email AS supervisor_email
                FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
                WHERE Supervisor_Name__Unsecured_ IS NOT NULL
                AND Supervisor_Email IS NOT NULL
            ),
            -- Map each employee to their supervisor AND their own supervisor_name format (if they are a supervisor)
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
            -- Recursive traversal: start with logged-in supervisor, find all reports down the chain
            downline AS (
                -- Base case: the logged-in supervisor themselves
                SELECT @supervisor_name AS supervisor_name, 0 AS level

                UNION ALL

                -- Recursive case: find employees who report to someone in our downline
                -- and who are themselves supervisors (have their own direct reports)
                SELECT sw.employee_supervisor_name AS supervisor_name, d.level + 1
                FROM staff_with_supervisor_format sw
                INNER JOIN downline d ON sw.reports_to = d.supervisor_name
                WHERE sw.employee_supervisor_name IS NOT NULL  -- Only include if they are a supervisor
                AND d.level < 10  -- Safety limit to prevent infinite recursion
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
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        accessible = [row.supervisor_name for row in results]
        logger.info(f"Found {len(accessible)} accessible supervisors for {supervisor_name}")
        return accessible

    except Exception as e:
        logger.error(f"Error fetching accessible supervisors for {supervisor_name}: {e}")
        # Fall back to just their own supervisor name
        return [supervisor_name] if supervisor_name else []


# ============================================
# Authentication Routes
# ============================================

@app.route('/login')
def login():
    """Initiate Google OAuth flow"""
    # Dev mode - auto authenticate
    if DEV_MODE:
        logger.info(f"DEV MODE: Auto-authenticating as {DEV_USER_EMAIL}")
        email = DEV_USER_EMAIL
        supervisor_name = get_supervisor_name_for_email(email)
        accessible_supervisors = get_accessible_supervisors(email, supervisor_name)

        session['user'] = {
            'email': email,
            'name': 'Dev User',
            'picture': '',
            'supervisor_name': supervisor_name,
            'is_admin': is_admin(email),
            'accessible_supervisors': accessible_supervisors
        }
        return redirect('/')

    # Build redirect URI based on request
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Google"""
    try:
        token = google.authorize_access_token()
        userinfo = token.get('userinfo')

        if not userinfo:
            logger.error("No userinfo in token")
            return redirect('/?error=auth_failed')

        email = userinfo.get('email', '')
        domain = email.split('@')[-1] if '@' in email else ''

        # Verify domain
        if domain.lower() != ALLOWED_DOMAIN.lower():
            logger.warning(f"Unauthorized domain attempt: {email}")
            return redirect(f'/?error=unauthorized_domain&domain={domain}')

        # Look up supervisor name for this email
        supervisor_name = get_supervisor_name_for_email(email)

        # Get list of all supervisors this user can access (hierarchical)
        accessible_supervisors = get_accessible_supervisors(email, supervisor_name)

        # Store user info in session
        session['user'] = {
            'email': email,
            'name': userinfo.get('name', ''),
            'picture': userinfo.get('picture', ''),
            'supervisor_name': supervisor_name,
            'is_admin': is_admin(email),
            'accessible_supervisors': accessible_supervisors
        }

        logger.info(f"User authenticated: {email}, supervisor: {supervisor_name}, "
                    f"accessible: {len(accessible_supervisors)} supervisors, admin: {is_admin(email)}")
        return redirect('/')

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect('/?error=auth_failed')


@app.route('/logout')
def logout():
    """Clear session and log out user"""
    session.clear()
    return redirect('/')


@app.route('/api/auth/status')
def auth_status():
    """Return current authentication status"""
    if 'user' in session:
        return jsonify({
            'authenticated': True,
            'user': session['user']
        })
    return jsonify({
        'authenticated': False,
        'user': None
    })


# ============================================
# Application Routes
# ============================================

@app.route('/')
def index():
    """Serve the main dashboard HTML file"""
    return send_from_directory('.', 'index.html')


@app.route('/api/supervisors', methods=['GET'])
@login_required
def get_supervisors():
    """
    Get list of supervisors the logged-in user can access.
    - Admins get all supervisors
    - Regular supervisors get themselves + their downline (hierarchical access)
    Returns: JSON array of supervisor names the user can view.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        user = session.get('user', {})
        accessible_supervisors = user.get('accessible_supervisors', [])

        if accessible_supervisors:
            logger.info(f"Returning {len(accessible_supervisors)} accessible supervisors for {user.get('email')}")
            return jsonify(accessible_supervisors)

        # If no accessible supervisors, return empty list
        logger.warning(f"No accessible supervisors for user: {user.get('email')}")
        return jsonify([])

    except Exception as e:
        logger.error(f"Error fetching supervisors: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh-session', methods=['POST'])
@login_required
def refresh_session():
    """
    Refresh the user's session data by recalculating accessible supervisors.
    This is useful when supervisor hierarchy data changes without requiring re-login.
    """
    try:
        user = session.get('user', {})
        email = user.get('email')

        if not email:
            return jsonify({'error': 'No user email in session'}), 400

        # Recalculate supervisor name and accessible supervisors
        supervisor_name = get_supervisor_name_for_email(email)
        accessible_supervisors = get_accessible_supervisors(email, supervisor_name)

        # Update session
        session['user'] = {
            'email': email,
            'supervisor_name': supervisor_name,
            'is_admin': is_admin(email),
            'accessible_supervisors': accessible_supervisors
        }

        logger.info(f"Session refreshed for {email}: {len(accessible_supervisors)} accessible supervisors")

        return jsonify({
            'success': True,
            'supervisor_name': supervisor_name,
            'accessible_supervisors': accessible_supervisors,
            'count': len(accessible_supervisors)
        })

    except Exception as e:
        logger.error(f"Error refreshing session: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/staff/<supervisor_name>', methods=['GET'])
@login_required
def get_staff(supervisor_name):
    """
    Get all staff members for a specific supervisor.
    Authorization: User can only access supervisors in their accessible list
    (their own team + downline, or all if admin).
    Args:
        supervisor_name: Name of the supervisor
    Returns: JSON array of staff records with all fields
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    # Authorization check: user can only access supervisors in their accessible list
    user = session.get('user', {})
    accessible_supervisors = user.get('accessible_supervisors', [])

    if supervisor_name not in accessible_supervisors:
        logger.warning(
            f"Authorization denied: user {user.get('email')} "
            f"tried to access {supervisor_name} (not in their {len(accessible_supervisors)} accessible supervisors)"
        )
        return jsonify({'error': 'Access denied. You do not have permission to view this team.'}), 403

    try:
        query = f"""
            WITH latest_accruals AS (
                SELECT
                    Person_Number,
                    Accrual_Code_Name,
                    (Earned_to_Date__Hours_ + Pending_Grants__Hours_) as max_hours,
                    (Earned_to_Date__Hours_ + Pending_Grants__Hours_ - COALESCE(Taken_to_Date__Hours_, 0)) as remaining_hours
                FROM `{PROJECT_ID}.payroll_validation.accrual_balance_native`
                WHERE Date_Balance_as_of_Date = (
                    SELECT MAX(Date_Balance_as_of_Date)
                    FROM `{PROJECT_ID}.payroll_validation.accrual_balance_native`
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
            )
            SELECT
                s.*,
                CONCAT(s.first_name, ' ', s.last_name) AS Staff_Name,
                a.pto_available,
                a.pto_max,
                a.vacation_available,
                a.vacation_max,
                a.personal_available,
                a.personal_max,
                a.sick_available,
                a.sick_max,
                sml.Salary_or_Hourly
            FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` s
            LEFT JOIN accrual_pivoted a ON s.Employee_Number = a.Person_Number
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` sml
                ON LOWER(s.Email_Address) = LOWER(sml.Email_Address)
            WHERE s.Supervisor_Name__Unsecured_ = @supervisor
            ORDER BY s.last_name, s.first_name
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("supervisor", "STRING", supervisor_name)
            ]
        )

        logger.info(f"Fetching staff data for supervisor: {supervisor_name}")
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        # Convert results to list of dictionaries
        staff_data = []
        for row in results:
            staff_member = dict(row.items())

            # Convert date/datetime objects to strings for JSON serialization
            for key, value in staff_member.items():
                if hasattr(value, 'isoformat'):
                    staff_member[key] = value.isoformat()

            staff_data.append(staff_member)

        logger.info(f"Found {len(staff_data)} staff members for {supervisor_name}")

        return jsonify(staff_data)

    except Exception as e:
        logger.error(f"Error fetching staff for {supervisor_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/itr-detail/<email>', methods=['GET'])
@login_required
def get_itr_detail(email):
    """
    Get Intent to Return detail for a specific employee by email.
    Returns detailed ITR survey response data from native table.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        # Query the native table directly (avoids Google Sheets permission issues)
        query = """
            SELECT
                Email_Address,
                Timestamp,
                Return,
                Return_Role,
                Return_Role_Preference,
                Return_Role_Preference_Other,
                -- Yes responses
                Yes_Decision_Factors,
                Yes_NPS,
                Yes_Top_Factors_Recommend_FLS,
                Yes_Adult_Culture_Open,
                Yes_Improve_Retention_Open,
                -- Maybe/Unsure responses
                Maybe_Decision_Factors,
                Maybe_NPS,
                Maybe_Top_Factors_Recommend_FLS,
                Maybe_Adult_Culture_Open,
                Maybe_Improve_Retention_Open,
                -- No responses
                No_Decision_Factors,
                No_NPS,
                No_Top_Factors_Recommend_FLS,
                No_Adult_Culture_Open,
                No_Improve_Retention_Open
            FROM `talent-demo-482004.intent_to_return.intent_to_return_native`
            WHERE LOWER(Email_Address) = LOWER(@email)
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )

        logger.info(f"Fetching ITR detail for: {email}")
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        if not results:
            return jsonify({'error': 'No ITR data found for this employee'}), 404

        row = results[0]
        intent = row.Return  # Yes, No, or Unsure

        # Select the appropriate fields based on the response type
        if intent == 'Yes':
            nps_score = row.Yes_NPS
            decision_factors = row.Yes_Decision_Factors
            top_factors = row.Yes_Top_Factors_Recommend_FLS
            culture_feedback = row.Yes_Adult_Culture_Open
            retention_feedback = row.Yes_Improve_Retention_Open
        elif intent == 'No':
            nps_score = row.No_NPS
            decision_factors = row.No_Decision_Factors
            top_factors = row.No_Top_Factors_Recommend_FLS
            culture_feedback = row.No_Adult_Culture_Open
            retention_feedback = row.No_Improve_Retention_Open
        else:  # Unsure/Maybe
            nps_score = row.Maybe_NPS
            decision_factors = row.Maybe_Decision_Factors
            top_factors = row.Maybe_Top_Factors_Recommend_FLS
            culture_feedback = row.Maybe_Adult_Culture_Open
            retention_feedback = row.Maybe_Improve_Retention_Open

        # Determine NPS category
        nps_category = None
        if nps_score is not None:
            if nps_score >= 9:
                nps_category = 'Promoter'
            elif nps_score >= 7:
                nps_category = 'Passive'
            else:
                nps_category = 'Detractor'

        itr_data = {
            'email': row.Email_Address,
            'response_date': row.Timestamp.isoformat() if row.Timestamp else None,
            'intent_to_return': intent,
            'return_role': row.Return_Role,
            'return_role_preference': row.Return_Role_Preference,
            'return_role_preference_other': row.Return_Role_Preference_Other,
            'nps_score': nps_score,
            'nps_category': nps_category,
            'decision_factors': decision_factors,
            'top_factors_recommend_fls': top_factors,
            'adult_culture_feedback': culture_feedback,
            'improve_retention_feedback': retention_feedback
        }

        logger.info(f"Found ITR data for {email}: intent={intent}")
        return jsonify(itr_data)

    except Exception as e:
        logger.error(f"Error fetching ITR detail for {email}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cert-status', methods=['GET'])
@login_required
def get_cert_status():
    """
    Get certification status for all teachers and leaders.
    Returns a dict of email -> certification info for staff who are certified.
    Only includes teachers and leadership roles (not network/support staff).
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        query = """
            SELECT
                LOWER(FLS_Email) as email,
                certification_status,
                active_certifications,
                active_qualifications,
                earliest_active_expiration,
                days_until_earliest_expiration
            FROM `talent-demo-482004.talent_certification.staff_with_certifications_native`
            WHERE certification_status = 'Certified'
            AND (
                Title LIKE '%Teacher%'
                OR Title LIKE '%Principal%'
                OR Title LIKE '%Dean%'
                OR Title LIKE '%Director%'
                OR Title LIKE '%Content Lead%'
            )
        """

        logger.info("Fetching certification status for teachers/leaders")
        query_job = client.query(query)
        results = query_job.result()

        # Build dict of email -> cert info
        cert_status = {}
        for row in results:
            cert_status[row.email] = {
                'status': row.certification_status,
                'active_count': row.active_certifications,
                'qualifications': row.active_qualifications,
                'earliest_expiration': row.earliest_active_expiration.isoformat() if row.earliest_active_expiration else None,
                'days_until_expiration': row.days_until_earliest_expiration
            }

        logger.info(f"Found {len(cert_status)} certified teachers/leaders")
        return jsonify(cert_status)

    except Exception as e:
        logger.error(f"Error fetching certification status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cert-detail/<email>', methods=['GET'])
@login_required
def get_cert_detail(email):
    """
    Get detailed certification information for a specific staff member.
    Returns all certifications (active and expired) for the popup modal.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        # First get summary info
        summary_query = """
            SELECT
                First_Name,
                Last_Name,
                Title,
                School_Site,
                certification_status,
                total_certifications,
                active_certifications,
                expired_certifications,
                active_qualifications,
                earliest_active_expiration,
                days_until_earliest_expiration
            FROM `talent-demo-482004.talent_certification.staff_with_certifications_native`
            WHERE LOWER(FLS_Email) = LOWER(@email)
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )

        query_job = client.query(summary_query, job_config=job_config)
        summary_results = list(query_job.result())

        if not summary_results:
            return jsonify({'error': 'No certification data found for this employee'}), 404

        summary = summary_results[0]

        # Get detailed certifications
        detail_query = """
            SELECT
                Category_Name,
                Qualification_Name,
                Certification_Number,
                Status,
                Earn_Date,
                Expire_Date,
                days_until_expiration,
                expiration_status
            FROM `talent-demo-482004.talent_certification.staff_certifications_detail_native`
            WHERE LOWER(FLS_Email) = LOWER(@email)
            ORDER BY
                CASE WHEN Status = 'Active' THEN 0 ELSE 1 END,
                Expire_Date DESC
        """

        query_job = client.query(detail_query, job_config=job_config)
        detail_results = query_job.result()

        certifications = []
        for row in detail_results:
            certifications.append({
                'category': row.Category_Name,
                'qualification': row.Qualification_Name,
                'certification_number': row.Certification_Number,
                'status': row.Status,
                'earn_date': row.Earn_Date.isoformat() if row.Earn_Date else None,
                'expire_date': row.Expire_Date.isoformat() if row.Expire_Date else None,
                'days_until_expiration': row.days_until_expiration,
                'expiration_status': row.expiration_status
            })

        cert_data = {
            'name': f"{summary.First_Name} {summary.Last_Name}",
            'title': summary.Title,
            'school': summary.School_Site,
            'certification_status': summary.certification_status,
            'total_certifications': summary.total_certifications,
            'active_certifications': summary.active_certifications,
            'expired_certifications': summary.expired_certifications,
            'active_qualifications': summary.active_qualifications,
            'earliest_expiration': summary.earliest_active_expiration.isoformat() if summary.earliest_active_expiration else None,
            'days_until_expiration': summary.days_until_earliest_expiration,
            'certifications': certifications
        }

        logger.info(f"Found {len(certifications)} certifications for {email}")
        return jsonify(cert_data)

    except Exception as e:
        logger.error(f"Error fetching certification detail for {email}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/orgchart')
def orgchart():
    """Serve the organization chart HTML file (Google Charts version)"""
    return send_from_directory('.', 'orgchart.html')


@app.route('/api/orgchart', methods=['GET'])
def get_orgchart_data():
    """
    Get organization chart data - all managers/supervisors with hierarchy info.
    Returns: JSON array of managers with their reporting relationships.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        query = f"""
            WITH
            -- Get all unique supervisor names (how they appear when someone reports to them)
            supervisor_names AS (
                SELECT DISTINCT Supervisor_Name__Unsecured_ as supervisor_key
                FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
                WHERE Employment_Status IN ('Active', 'Leave of absence')
                AND Supervisor_Name__Unsecured_ IS NOT NULL
                AND Salary_or_Hourly = 'Salaried'
            ),
            -- Get names of C-level executives (Chiefs)
            c_level_names AS (
                SELECT DISTINCT
                    COALESCE(sn.supervisor_key, CONCAT(s.Last_Name, ', ', s.First_Name)) as chief_name
                FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` s
                LEFT JOIN supervisor_names sn
                    ON LOWER(sn.supervisor_key) LIKE CONCAT(LOWER(s.Last_Name), ', ', LOWER(s.First_Name), '%')
                WHERE s.Employment_Status IN ('Active', 'Leave of absence')
                AND s.Job_Title LIKE '%Chief%'
                AND s.Salary_or_Hourly = 'Salaried'
            ),
            -- Get staff with their supervisor name format using LEFT JOIN
            all_staff AS (
                SELECT
                    CASE
                        WHEN s.Preferred_First_Name IS NOT NULL
                             AND s.Preferred_First_Name != ''
                             AND LOWER(s.Preferred_First_Name) != LOWER(s.Last_Name)
                        THEN s.Preferred_First_Name
                        ELSE s.First_Name
                    END as first_name,
                    s.Last_Name as last_name,
                    CONCAT(
                        CASE
                            WHEN s.Preferred_First_Name IS NOT NULL
                                 AND s.Preferred_First_Name != ''
                                 AND LOWER(s.Preferred_First_Name) != LOWER(s.Last_Name)
                            THEN s.Preferred_First_Name
                            ELSE s.First_Name
                        END,
                        ' ', s.Last_Name
                    ) as full_name,
                    s.Job_Title as job_title,
                    s.Dept as dept,
                    s.Employment_Status as employment_status,
                    COALESCE(s.Supervisor_Name__Unsecured_, '') as reports_to,
                    -- Use the matched supervisor_key format, or fall back to simple format
                    COALESCE(sn.supervisor_key, CONCAT(s.Last_Name, ', ', s.First_Name)) as name_key
                FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function` s
                LEFT JOIN supervisor_names sn
                    ON LOWER(sn.supervisor_key) LIKE CONCAT(LOWER(s.Last_Name), ', ', LOWER(s.First_Name), '%')
                WHERE s.Employment_Status IN ('Active', 'Leave of absence')
                AND s.Salary_or_Hourly = 'Salaried'
            ),
            -- Count direct reports per supervisor (salaried only)
            report_counts AS (
                SELECT
                    Supervisor_Name__Unsecured_ as supervisor_key,
                    COUNT(*) as direct_reports
                FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
                WHERE Employment_Status IN ('Active', 'Leave of absence')
                AND Supervisor_Name__Unsecured_ IS NOT NULL
                AND Salary_or_Hourly = 'Salaried'
                GROUP BY Supervisor_Name__Unsecured_
            ),
            -- Get manager name keys (people with Manager in title)
            manager_names AS (
                SELECT DISTINCT name_key
                FROM all_staff
                WHERE job_title LIKE '%Manager%'
            ),
            -- Get director name keys (people with Director/Dir in title)
            director_names AS (
                SELECT DISTINCT name_key
                FROM all_staff
                WHERE job_title LIKE '%Director%' OR job_title LIKE '%Dir %' OR job_title LIKE 'Dir of%'
            ),
            -- Select managers (supervisors, leadership, OR direct reports of C-level/Managers/Directors)
            managers AS (
                SELECT DISTINCT
                    s.name_key,
                    s.full_name,
                    s.first_name,
                    s.last_name,
                    s.job_title,
                    s.dept,
                    s.employment_status,
                    s.reports_to,
                    COALESCE(rc.direct_reports, 0) as direct_reports
                FROM all_staff s
                LEFT JOIN report_counts rc ON s.name_key = rc.supervisor_key
                WHERE s.name_key IN (SELECT supervisor_key FROM supervisor_names)
                   OR s.reports_to IS NULL
                   OR s.reports_to = ''
                   OR s.job_title LIKE '%Chief%'
                   OR s.job_title LIKE '%Director%'
                   OR s.job_title LIKE '%ExDir%'
                   OR s.job_title LIKE '%Manager%'
                   OR s.reports_to IN (SELECT chief_name FROM c_level_names)
                   OR s.reports_to IN (SELECT name_key FROM manager_names)
                   OR s.reports_to IN (SELECT name_key FROM director_names)
            )
            SELECT * FROM managers
            ORDER BY
                CASE WHEN job_title LIKE '%CEO%' OR job_title LIKE '%Executive%' THEN 0
                     WHEN job_title LIKE '%Chief%' THEN 1
                     WHEN job_title LIKE '%ExDir%' THEN 2
                     WHEN job_title LIKE '%Director%' THEN 3
                     WHEN job_title LIKE '%Principal%' AND job_title NOT LIKE '%Asst%' THEN 4
                     WHEN job_title LIKE '%Asst Principal%' THEN 5
                     ELSE 6 END,
                last_name
        """

        logger.info("Fetching org chart data")
        query_job = client.query(query)
        results = query_job.result()

        # Convert results to list of dictionaries
        org_data = []
        for row in results:
            org_data.append({
                'name_key': row.name_key,
                'full_name': row.full_name,
                'first_name': row.first_name,
                'last_name': row.last_name,
                'job_title': row.job_title,
                'dept': row.dept,
                'employment_status': row.employment_status,
                'reports_to': row.reports_to,
                'direct_reports': row.direct_reports
            })

        logger.info(f"Found {len(org_data)} managers for org chart")
        return jsonify(org_data)

    except Exception as e:
        logger.error(f"Error fetching org chart data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/staff-reports/<supervisor_name>', methods=['GET'])
def get_staff_reports(supervisor_name):
    """
    Get all direct reports for a supervisor (for org chart popup).
    Returns all staff who report to this person, not just managers.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        query = f"""
            SELECT
                CASE
                    WHEN Preferred_First_Name IS NOT NULL
                         AND Preferred_First_Name != ''
                         AND LOWER(Preferred_First_Name) != LOWER(Last_Name)
                    THEN Preferred_First_Name
                    ELSE First_Name
                END as First_Name,
                Last_Name,
                CONCAT(
                    CASE
                        WHEN Preferred_First_Name IS NOT NULL
                             AND Preferred_First_Name != ''
                             AND LOWER(Preferred_First_Name) != LOWER(Last_Name)
                        THEN Preferred_First_Name
                        ELSE First_Name
                    END,
                    ' ', Last_Name
                ) as full_name,
                Job_Title,
                Employment_Status
            FROM `{PROJECT_ID}.{DATASET_ID}.staff_master_list_with_function`
            WHERE Supervisor_Name__Unsecured_ = @supervisor
            AND Employment_Status IN ('Active', 'Leave of absence')
            ORDER BY Last_Name, First_Name
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("supervisor", "STRING", supervisor_name)
            ]
        )

        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        staff = []
        for row in results:
            staff.append({
                'first_name': row.First_Name,
                'last_name': row.Last_Name,
                'full_name': row.full_name,
                'job_title': row.Job_Title,
                'employment_status': row.Employment_Status
            })

        return jsonify(staff)

    except Exception as e:
        logger.error(f"Error fetching staff reports for {supervisor_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/action-steps/<supervisor_name>', methods=['GET'])
@login_required
def get_action_steps(supervisor_name):
    """
    Get the most recent action step for each staff member under a supervisor.
    Returns a dict of email -> action step info.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    # Verify access
    user = session.get('user', {})
    accessible_supervisors = user.get('accessible_supervisors', [])

    if not is_admin(user.get('email', '')) and supervisor_name not in accessible_supervisors:
        logger.warning(f"Access denied: {user.get('email')} tried to access {supervisor_name}'s action steps")
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Get all action steps for each staff member (current school year)
        query = """
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
            FROM `talent-demo-482004.talent_grow_observations.ldg_action_steps` a
            INNER JOIN `talent-demo-482004.talent_grow_observations.staff_master_list_with_function` s
                ON LOWER(a.user_email) = LOWER(s.Email_Address)
            WHERE s.Supervisor_Name__Unsecured_ = @supervisor_name
            AND a.archivedAt IS NULL
            AND a.created >= '2025-07-01'
            ORDER BY a.user_email, a.created DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("supervisor_name", "STRING", supervisor_name)
            ]
        )

        logger.info(f"Fetching action steps for supervisor: {supervisor_name}")
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        # Build dict of email -> list of action steps
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

        logger.info(f"Found action steps for {len(action_steps)} staff members for {supervisor_name}")
        return jsonify(action_steps)

    except Exception as e:
        logger.error(f"Error fetching action steps for {supervisor_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/observations/<email>', methods=['GET'])
@login_required
def get_observations(email):
    """
    Get observation history for a specific staff member.
    Returns a list of observations with details.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    try:
        # Get unique observations for this staff member (current school year)
        # Use aggregation to ensure we get the observation_link (some rows may have NULL)
        query = """
            SELECT
                teacher_email,
                teacher_name,
                observer_name,
                observation_type,
                observed_at,
                rubric_form,
                school_when_observed,
                MAX(observation_link) as observation_link
            FROM `talent-demo-482004.talent_grow_observations.observations_raw_native`
            WHERE LOWER(teacher_email) = LOWER(@email)
            AND observed_at >= '2025-07-01'
            AND is_published = 1
            GROUP BY teacher_email, teacher_name, observer_name, observation_type, observed_at, rubric_form, school_when_observed
            ORDER BY observed_at DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", email)
            ]
        )

        logger.info(f"Fetching observations for: {email}")
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        # Build list of observations (already deduplicated by SQL GROUP BY)
        observations = []
        for row in results:
            # Fix the observation link domain (schoolmint -> leveldata)
            link = row.observation_link
            if link:
                link = link.replace('schoolmint', 'leveldata')

            observations.append({
                'teacher_name': row.teacher_name,
                'observer_name': row.observer_name,
                'observation_type': row.observation_type,
                'observed_at': row.observed_at.isoformat() if row.observed_at else None,
                'rubric_form': row.rubric_form,
                'school': row.school_when_observed,
                'link': link
            })

        logger.info(f"Found {len(observations)} observations for {email}")
        return jsonify(observations)

    except Exception as e:
        logger.error(f"Error fetching observations for {email}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/meetings/<supervisor_name>', methods=['GET'])
@login_required
def get_meetings(supervisor_name):
    """
    Get the most recent meetings for each staff member under a supervisor.
    Returns a dict of email -> list of meetings.
    """
    if not client:
        return jsonify({'error': 'BigQuery client not initialized'}), 500

    # Verify access
    user = session.get('user', {})
    accessible_supervisors = user.get('accessible_supervisors', [])

    if not is_admin(user.get('email', '')) and supervisor_name not in accessible_supervisors:
        logger.warning(f"Access denied: {user.get('email')} tried to access {supervisor_name}'s meetings")
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Get meetings where the staff member was a participant (current school year)
        query = """
            WITH staff_emails AS (
                SELECT LOWER(Email_Address) as email
                FROM `talent-demo-482004.talent_grow_observations.staff_master_list_with_function`
                WHERE Supervisor_Name__Unsecured_ = @supervisor_name
                AND Employment_Status IN ('Active', 'Leave of absence')
            ),
            meetings_with_staff AS (
                SELECT
                    m._id,
                    m.title,
                    m.date,
                    m.creator_name,
                    m.creator_email,
                    m.participant_names,
                    m.participant_emails,
                    m.type_name,
                    m.what_was_discussed,
                    m.next_steps,
                    m.created,
                    LOWER(TRIM(pe)) as staff_email
                FROM `talent-demo-482004.talent_grow_observations.ldg_meetings` m,
                UNNEST(SPLIT(m.participant_emails, ', ')) as pe
                WHERE m.created >= '2025-07-01'
                AND m.archivedAt IS NULL
            )
            SELECT
                mws.*
            FROM meetings_with_staff mws
            INNER JOIN staff_emails se ON mws.staff_email = se.email
            ORDER BY mws.staff_email, mws.date DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("supervisor_name", "STRING", supervisor_name)
            ]
        )

        logger.info(f"Fetching meetings for supervisor: {supervisor_name}")
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        # Build dict of email -> list of meetings
        meetings = {}
        for row in results:
            email = row.staff_email if row.staff_email else ''
            meeting = {
                'id': row._id,
                'title': row.title,
                'date': row.date.isoformat() if row.date else None,
                'creator_name': row.creator_name,
                'creator_email': row.creator_email,
                'participant_names': row.participant_names,
                'type_name': row.type_name,
                'what_was_discussed': row.what_was_discussed[:500] if row.what_was_discussed else None,  # Truncate for list
                'next_steps': row.next_steps[:500] if row.next_steps else None,
                'created': row.created.isoformat() if row.created else None
            }
            if email not in meetings:
                meetings[email] = []
            meetings[email].append(meeting)

        logger.info(f"Found meetings for {len(meetings)} staff members for {supervisor_name}")
        return jsonify(meetings)

    except Exception as e:
        logger.error(f"Error fetching meetings for {supervisor_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bigquery_connected': client is not None
    })


if __name__ == '__main__':
    # Check if BigQuery client is initialized
    if not client:
        logger.warning("BigQuery client is not initialized. Please check your credentials.")
        logger.warning("Run: gcloud auth application-default login")

    # Get port from environment variable (Cloud Run sets this)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

    # Run Flask app
    logger.info(f"Starting Flask server on http://localhost:{port}")
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
