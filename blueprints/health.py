"""Health check blueprint."""

from flask import Blueprint, jsonify
from extensions import bq_client

bp = Blueprint('health', __name__)


@bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bigquery_connected': bq_client is not None
    })
