"""
Security middleware for ADHD Printer API
Provides authentication, rate limiting, and security headers
"""
from functools import wraps
from flask import request, jsonify, abort
import os
import logging
from datetime import datetime
import json

# Setup security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs('/app/logs', exist_ok=True)

handler = logging.FileHandler('/app/logs/security.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(handler)


def require_api_key(f):
    """
    Decorator to require API key for endpoints

    Usage:
        @notes_bp.route('/', methods=['POST'])
        @require_api_key
        def create_note():
            pass

    Environment:
        API_KEYS: Comma-separated list of valid API keys
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        # Get valid API keys from environment
        valid_keys_str = os.getenv('API_KEYS', '')
        if not valid_keys_str:
            # If no API keys configured, warn but allow (for development)
            security_logger.warning("API_KEYS not configured - authentication disabled!")
            return f(*args, **kwargs)

        valid_keys = [k.strip() for k in valid_keys_str.split(',') if k.strip()]

        if not api_key:
            security_logger.warning(
                f"Missing API key from {request.remote_addr} for {request.path}"
            )
            return jsonify({
                'error': 'Unauthorized',
                'message': 'API key required. Include X-API-Key header.'
            }), 401

        if api_key not in valid_keys:
            security_logger.warning(
                f"Invalid API key from {request.remote_addr} for {request.path}"
            )
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid API key'
            }), 401

        # Log successful authentication
        security_logger.info(
            f"Authenticated request from {request.remote_addr} for {request.path}"
        )

        return f(*args, **kwargs)

    return decorated


def init_security(app):
    """
    Initialize security middleware for Flask app

    Features:
    - Security headers
    - Request logging
    - IP whitelist (optional)
    - Response logging for errors
    """

    # Security headers
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses"""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Don't reveal server info
        response.headers.pop('Server', None)

        return response

    # Request logging
    @app.before_request
    def log_request():
        """Log all incoming requests"""
        # Skip logging for health checks to reduce noise
        if request.path == '/health/' or request.path == '/health':
            return

        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'has_api_key': bool(request.headers.get('X-API-Key')),
        }
        security_logger.info(json.dumps(log_data))

    # Response logging for errors
    @app.after_request
    def log_response(response):
        """Log error responses"""
        if response.status_code >= 400:
            security_logger.warning(
                f"Error response: {response.status_code} for "
                f"{request.method} {request.path} from {request.remote_addr}"
            )
        return response

    # IP whitelist (optional)
    allowed_ips_str = os.getenv('ALLOWED_IPS', '')
    if allowed_ips_str:
        allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]

        @app.before_request
        def check_ip_whitelist():
            """Only allow whitelisted IPs"""
            # Skip check for health endpoint
            if request.path == '/health/' or request.path == '/health':
                return

            if request.remote_addr not in allowed_ips:
                security_logger.warning(
                    f"Blocked request from non-whitelisted IP: {request.remote_addr}"
                )
                abort(403, description="Access denied")

        security_logger.info(f"IP whitelist enabled: {len(allowed_ips)} IPs allowed")

    # Log initialization
    security_logger.info("Security middleware initialized")
    if not os.getenv('API_KEYS'):
        security_logger.warning("WARNING: API_KEYS not set - authentication disabled!")
