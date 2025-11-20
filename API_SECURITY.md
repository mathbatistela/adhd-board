# API Security Guide for ADHD Printer Backend

This guide covers how to protect your Flask backend API from unauthorized access and abuse.

## Current Security Status

Your backend currently has:
- ✅ CORS configuration
- ✅ Input validation (Marshmallow schemas)
- ✅ Docker isolation
- ⚠️ No authentication
- ⚠️ No rate limiting
- ⚠️ No API keys
- ⚠️ No request logging

## Security Layers

### Layer 1: Network-Level Protection (Infrastructure)
### Layer 2: Application-Level Protection (Code)
### Layer 3: Monitoring & Logging (Detection)

---

## Layer 1: Network-Level Protection

### Option A: Reverse Proxy (Recommended)

Use nginx/Traefik to:
- Hide backend from direct access
- Rate limit requests
- Block suspicious IPs
- Add security headers

**Already covered in:** `PORTAINER_DEPLOYMENT.md` Option 2

### Option B: Firewall Rules

If using Option 1 (direct exposure):

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow only specific IPs to API (example)
sudo ufw allow from 203.0.113.0/24 to any port 5000

# Or allow from your network only
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Enable firewall
sudo ufw enable
```

### Option C: VPN/Tailscale (Best for Homelab)

Keep API completely private, only accessible via VPN:

1. Install Tailscale on server and devices
2. Don't expose port 5000 publicly
3. Use Tailscale IP: `VITE_API_URL=http://100.x.x.x:5000/api`

**Pros:** Most secure, no port forwarding needed
**Cons:** Users need Tailscale installed

---

## Layer 2: Application-Level Protection

### 1. API Key Authentication

Simple token-based auth for your personal use.

**File:** `backend/app/middleware/auth.py`

```python
from functools import wraps
from flask import request, jsonify
import os

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        # Get valid API keys from environment
        valid_keys = os.getenv('API_KEYS', '').split(',')

        if not api_key or api_key not in valid_keys:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key required'
            }), 401

        return f(*args, **kwargs)
    return decorated_function
```

**Usage in endpoints:**

```python
from app.middleware.auth import require_api_key

@notes_bp.route('/', methods=['POST'])
@require_api_key  # Add this decorator
@notes_bp.arguments(NoteCreateSchema)
@notes_bp.response(201, NoteResponseSchema)
def create_note(note_data):
    """Create a new note"""
    # ... existing code
```

**Environment variable:**

```env
# Generate with: openssl rand -hex 32
API_KEYS=your-secret-key-1,your-secret-key-2,your-secret-key-3
```

**Frontend usage:**

```typescript
// src/lib/api.ts
const API_KEY = import.meta.env.VITE_API_KEY;

export const apiClient = {
  async createNote(data: NoteCreate) {
    const response = await fetch(`${API_BASE_URL}/notes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,  // Add API key header
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },
  // ... other methods
};
```

**Frontend .env:**
```env
VITE_API_KEY=your-secret-key-1
```

### 2. Rate Limiting

Prevent abuse by limiting requests per IP.

**Install dependency:**

```bash
pip install flask-limiter
```

**File:** `backend/app/__init__.py`

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Use Redis in production
)

# Apply to specific blueprints
from app.api import notes_bp
limiter.limit("30 per minute")(notes_bp)
```

**Per-endpoint limits:**

```python
@notes_bp.route('/', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter limit for creation
@notes_bp.arguments(NoteCreateSchema)
def create_note(note_data):
    # ... existing code
```

**With Redis (production):**

```python
# docker-compose.yml
services:
  redis:
    image: redis:alpine
    restart: unless-stopped

# app/__init__.py
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://redis:6379",
)
```

### 3. CORS Hardening

Replace wildcard with specific origins:

```python
# config.py
class Config(BaseSettings):
    # Don't use * in production
    CORS_ORIGINS: str = Field(
        default="http://localhost:8080",
        description="Comma-separated list of allowed origins"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

# app/__init__.py
from flask_cors import CORS

CORS(app,
     origins=config.cors_origins_list,
     methods=['GET', 'POST', 'PUT', 'DELETE'],
     allow_headers=['Content-Type', 'X-API-Key'])
```

### 4. Input Validation & Sanitization

Already good with Marshmallow! But add extra checks:

```python
from bleach import clean

class NoteCreateSchema(Schema):
    category = fields.Str(required=True)
    text = fields.Str(required=True, validate=validate.Length(max=500))

    @validates('text')
    def validate_text(self, value):
        # Strip HTML tags
        cleaned = clean(value, tags=[], strip=True)
        if len(cleaned) > 500:
            raise ValidationError('Text too long')
        return cleaned

    @validates('category')
    def validate_category(self, value):
        allowed = ['trabalho', 'casa', 'urgente', 'lazer']
        if value not in allowed:
            raise ValidationError(f'Category must be one of: {allowed}')
        return value
```

### 5. Request Size Limits

```python
# config.py
class Config(BaseSettings):
    MAX_CONTENT_LENGTH: int = Field(
        default=16 * 1024 * 1024,  # 16 MB
        description="Max request size in bytes"
    )

# app/__init__.py
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
```

### 6. Security Headers

```python
from flask import Flask

@app.after_request
def set_security_headers(response):
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Content Security Policy (adjust for your needs)
    response.headers['Content-Security-Policy'] = "default-src 'self'"

    return response
```

### 7. Request Logging & Monitoring

```python
import logging
from flask import request
import json
from datetime import datetime

# Setup logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('/app/logs/security.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(handler)

@app.before_request
def log_request():
    """Log all API requests"""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'ip': request.remote_addr,
        'method': request.method,
        'path': request.path,
        'user_agent': request.headers.get('User-Agent'),
        'api_key_provided': bool(request.headers.get('X-API-Key'))
    }
    security_logger.info(json.dumps(log_data))

@app.after_request
def log_response(response):
    """Log response status"""
    if response.status_code >= 400:
        security_logger.warning(
            f"Error response: {response.status_code} for {request.path}"
        )
    return response
```

### 8. IP Whitelist (Optional)

For maximum security - only allow specific IPs:

```python
from flask import abort, request

ALLOWED_IPS = os.getenv('ALLOWED_IPS', '').split(',')

@app.before_request
def check_ip():
    """Only allow whitelisted IPs"""
    if ALLOWED_IPS and request.remote_addr not in ALLOWED_IPS:
        security_logger.warning(
            f"Blocked request from unauthorized IP: {request.remote_addr}"
        )
        abort(403)
```

```env
# Only allow these IPs
ALLOWED_IPS=192.168.1.100,192.168.1.101,203.0.113.10
```

---

## Layer 3: Monitoring & Detection

### 1. Fail2Ban for Brute Force Protection

**Install on host:**

```bash
sudo apt install fail2ban
```

**Create filter:** `/etc/fail2ban/filter.d/adhd-api.conf`

```ini
[Definition]
failregex = ^.*"ip": "<HOST>".*"status": 401.*$
            ^.*Blocked request from unauthorized IP: <HOST>.*$
ignoreregex =
```

**Create jail:** `/etc/fail2ban/jail.d/adhd-api.conf`

```ini
[adhd-api]
enabled = true
port = 5000
filter = adhd-api
logpath = /path/to/security.log
maxretry = 5
bantime = 3600
findtime = 600
```

```bash
sudo systemctl restart fail2ban
```

### 2. Log Analysis

**Parse logs for suspicious activity:**

```bash
# Count requests per IP
cat /app/logs/security.log | jq -r '.ip' | sort | uniq -c | sort -rn

# Find failed auth attempts
cat /app/logs/security.log | jq 'select(.status == 401)'

# Find unusual user agents
cat /app/logs/security.log | jq -r '.user_agent' | sort | uniq -c
```

### 3. Alerting

**Simple email alert on errors:**

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, body):
    """Send email alert"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'alerts@yourdomain.com'
    msg['To'] = 'admin@yourdomain.com'

    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)

@app.errorhandler(500)
def handle_500(error):
    send_alert(
        'API Error',
        f'500 error occurred: {error}\nIP: {request.remote_addr}'
    )
    return jsonify({'error': 'Internal server error'}), 500
```

---

## Complete Implementation Example

**File:** `backend/app/security.py`

```python
"""
Centralized security configuration
"""
from functools import wraps
from flask import request, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from datetime import datetime
import json

# Setup security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('/app/logs/security.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(handler)

# Rate limiter
limiter = None  # Initialize in create_app()

def init_security(app):
    """Initialize security middleware"""
    global limiter

    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.getenv('REDIS_URL', 'memory://'),
    )

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Request logging
    @app.before_request
    def log_request():
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent'),
        }
        security_logger.info(json.dumps(log_data))

    # IP whitelist (if configured)
    allowed_ips = os.getenv('ALLOWED_IPS', '').split(',')
    if allowed_ips and allowed_ips[0]:  # Check not empty
        @app.before_request
        def check_ip():
            if request.remote_addr not in allowed_ips:
                security_logger.warning(
                    f"Blocked unauthorized IP: {request.remote_addr}"
                )
                abort(403)

def require_api_key(f):
    """Decorator to require API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        valid_keys = os.getenv('API_KEYS', '').split(',')

        if not api_key or api_key not in valid_keys:
            security_logger.warning(
                f"Unauthorized API access attempt from {request.remote_addr}"
            )
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key required'
            }), 401

        return f(*args, **kwargs)
    return decorated
```

**Update:** `backend/app/__init__.py`

```python
from app.security import init_security, limiter, require_api_key

def create_app():
    app = Flask(__name__)

    # ... existing setup ...

    # Initialize security
    init_security(app)

    # Apply rate limits to blueprints
    from app.api import notes_bp
    limiter.limit("30 per minute")(notes_bp)

    return app
```

---

## Environment Variables Summary

```env
# API Keys (required for authentication)
API_KEYS=key1,key2,key3

# CORS (specific origins, not *)
CORS_ORIGINS=http://your-domain.com,https://your-domain.com

# IP Whitelist (optional, leave empty to allow all)
ALLOWED_IPS=192.168.1.100,203.0.113.10

# Rate Limiting (optional, use Redis in production)
REDIS_URL=redis://redis:6379

# Max request size
MAX_CONTENT_LENGTH=16777216

# Secret key (Flask sessions)
SECRET_KEY=your-random-secret-key
```

---

## Deployment Checklist

### Before Going Public:

- [ ] Set API_KEYS with strong random keys
- [ ] Configure CORS_ORIGINS (no wildcard)
- [ ] Enable HTTPS/TLS
- [ ] Set up rate limiting with Redis
- [ ] Configure fail2ban
- [ ] Set up log monitoring
- [ ] Enable firewall rules
- [ ] Test authentication works
- [ ] Test rate limits work
- [ ] Review security headers
- [ ] Set up alerts for errors
- [ ] Document API keys securely

### For Maximum Security:

- [ ] Use reverse proxy (Option 2)
- [ ] Keep backend on internal network
- [ ] Use VPN/Tailscale for access
- [ ] Enable IP whitelist
- [ ] Set up automated backups
- [ ] Regular security updates
- [ ] Monitor logs daily

---

## Quick Setup (Minimum Security)

For homelab with minimal setup:

1. **Add API key auth:**
   ```bash
   # Generate key
   openssl rand -hex 32

   # Add to .env
   echo "API_KEYS=your-generated-key" >> .env
   ```

2. **Update endpoints:**
   Add `@require_api_key` decorator to sensitive endpoints

3. **Set CORS:**
   ```env
   CORS_ORIGINS=http://your-ip:8080
   ```

4. **Add to frontend:**
   ```env
   # frontend/.env
   VITE_API_KEY=your-generated-key
   ```

That's it! You now have basic protection.

---

## Testing Security

```bash
# Test without API key (should fail)
curl -X POST http://localhost:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{"category": "test", "text": "test"}'

# Test with API key (should work)
curl -X POST http://localhost:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"category": "trabalho", "text": "test note"}'

# Test rate limiting (send 100 requests)
for i in {1..100}; do
  curl -X GET http://localhost:5000/api/notes/
done
# Should eventually get 429 Too Many Requests
```

---

## Further Improvements

### Advanced Authentication
- OAuth2 with GitHub/Google
- JWT tokens with refresh
- User accounts with sessions

### Advanced Monitoring
- Prometheus + Grafana
- ELK stack (Elasticsearch, Logstash, Kibana)
- Sentry for error tracking

### Advanced Rate Limiting
- Per-user limits (not just IP)
- Dynamic limits based on behavior
- Distributed rate limiting with Redis

### WAF (Web Application Firewall)
- ModSecurity
- Cloudflare WAF
- AWS WAF

---

## Summary

**Minimum (Homelab):**
- API key authentication
- CORS configuration
- Reverse proxy OR VPN

**Recommended (Public):**
- API key authentication
- Rate limiting
- CORS hardening
- Security headers
- Request logging
- Reverse proxy
- Fail2ban
- HTTPS

**Maximum (Production):**
- All of the above, plus:
- IP whitelist
- WAF
- Advanced monitoring
- Automated alerting
- Regular security audits

Choose based on your threat model and how public your deployment is!
