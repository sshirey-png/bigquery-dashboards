"""
Flask backend for Supervisor Dashboard
App factory + blueprint registration
"""

from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
import os

from config import SECRET_KEY, ALLOWED_ORIGINS, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from extensions import oauth, bq_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    # Fix for running behind Cloud Run proxy (ensures HTTPS redirect URIs)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Session configuration
    app.secret_key = SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') != 'development'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # CORS
    CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

    # OAuth
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    # Register blueprints (no url_prefix — route paths stay identical)
    from blueprints.health import bp as health_bp
    from blueprints.auth_routes import bp as auth_bp
    from blueprints.supervisor import bp as supervisor_bp
    from blueprints.hr import bp as hr_bp
    from blueprints.schools import bp as schools_bp
    from blueprints.kickboard import bp as kickboard_bp
    from blueprints.orgchart import bp as orgchart_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(supervisor_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(schools_bp)
    app.register_blueprint(kickboard_bp)
    app.register_blueprint(orgchart_bp)

    return app


# Module-level app for gunicorn: `gunicorn app:app`
app = create_app()

if __name__ == '__main__':
    if not bq_client:
        logger.warning("BigQuery client is not initialized. Please check your credentials.")
        logger.warning("Run: gcloud auth application-default login")

    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

    logger.info(f"Starting Flask server on http://localhost:{port}")
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
