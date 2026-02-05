"""Authentication routes: login, callback, logout, auth status."""

import logging
from flask import Blueprint, jsonify, redirect, url_for, session, request

from config import (
    ADMIN_EMAILS, EMAIL_ALIASES, ALLOWED_DOMAIN, DEV_MODE, DEV_USER_EMAIL,
)
from extensions import oauth
from auth import (
    is_admin, get_supervisor_name_for_email, get_accessible_supervisors,
    get_schools_dashboard_role, get_kickboard_access,
)

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)


@bp.route('/login')
def login():
    """Initiate Google OAuth flow"""
    next_url = request.args.get('next', '/')
    session['login_next'] = next_url

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
        return redirect(next_url)

    google = oauth.create_client('google')
    redirect_uri = url_for('auth.auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@bp.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Google"""
    try:
        google = oauth.create_client('google')
        token = google.authorize_access_token()
        userinfo = token.get('userinfo')

        if not userinfo:
            logger.error("No userinfo in token")
            return redirect('/?error=auth_failed')

        email = userinfo.get('email', '')
        domain = email.split('@')[-1] if '@' in email else ''

        is_aliased = email.lower() in EMAIL_ALIASES

        if domain.lower() != ALLOWED_DOMAIN.lower() and not is_aliased:
            logger.warning(f"Unauthorized domain attempt: {email}")
            return redirect(f'/?error=unauthorized_domain&domain={domain}')

        supervisor_name = get_supervisor_name_for_email(email)
        accessible_supervisors = get_accessible_supervisors(email, supervisor_name)

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
        next_url = session.pop('login_next', '/')
        return redirect(next_url)

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect('/?error=auth_failed')


@bp.route('/logout')
def logout():
    """Clear session and log out user"""
    session.clear()
    return redirect('/')


@bp.route('/api/auth/status')
def auth_status():
    """Return current authentication status"""
    if 'user' in session:
        user = session['user']
        user_email = user.get('email', '').lower()
        is_admin_flag = user_email in [e.lower() for e in ADMIN_EMAILS]
        schools_role = get_schools_dashboard_role(user_email)
        kickboard_access = get_kickboard_access(user_email)
        return jsonify({
            'authenticated': True,
            'user': user,
            'is_admin': is_admin_flag,
            'schools_dashboard_access': schools_role is not None,
            'schools_dashboard_role': schools_role,
            'kickboard_dashboard_access': kickboard_access is not None,
            'kickboard_access': kickboard_access
        })
    return jsonify({
        'authenticated': False,
        'user': None,
        'is_admin': False,
        'schools_dashboard_access': False,
        'schools_dashboard_role': None,
        'kickboard_dashboard_access': False,
        'kickboard_access': None
    })
