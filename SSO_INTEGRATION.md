# SSO Integration Guide for ADHD Printer

This guide explains how to protect your API using Single Sign-On (SSO) solutions like Pangolin, Authentik, Authelia, or Keycloak.

## Understanding SSO with Static Frontend + API

Your architecture:
- **Frontend:** Static React app (runs in browser)
- **Backend:** Flask API
- **SSO:** Authentication service

## SSO Flow

```
User
  ↓
Frontend (static site)
  ↓
SSO Service (Pangolin/Authentik/etc)
  ↓
Get JWT/Token
  ↓
Frontend stores token
  ↓
API requests include token
  ↓
Backend validates token
```

---

## Option 1: Pangolin SSO

Pangolin is a lightweight SSO solution written in Go.

### Architecture

```
┌──────────┐
│  User    │
└────┬─────┘
     │
     ▼
┌──────────────┐
│  Frontend    │ (http://your-domain.com)
│  (React)     │
└──────┬───────┘
       │
       ├─── Login click ──→ Redirect to Pangolin
       │
       ▼
┌──────────────┐
│  Pangolin    │ (http://auth.your-domain.com)
│  SSO         │ Validates credentials
└──────┬───────┘
       │
       ├─── Success ──→ Return JWT token
       │
       ▼
┌──────────────┐
│  Frontend    │ Stores token in localStorage
│              │ Includes token in API requests
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Backend     │ Validates JWT token
│  Flask API   │ Checks signature & expiry
└──────────────┘
```

### Backend Implementation

**Install dependencies:**

```bash
# requirements.txt
PyJWT==2.8.0
cryptography==41.0.7
```

**File:** `backend/app/middleware/sso_auth.py`

```python
"""
SSO authentication using JWT tokens
"""
from functools import wraps
from flask import request, jsonify
import jwt
import os
from datetime import datetime

def require_sso_auth(f):
    """
    Decorator to require valid JWT token from SSO

    Token should be in Authorization header:
    Authorization: Bearer <jwt-token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication token required'
            }), 401

        try:
            # Decode JWT token
            # IMPORTANT: Use the same secret key as your SSO service
            secret_key = os.getenv('SSO_SECRET_KEY')
            algorithm = os.getenv('SSO_ALGORITHM', 'HS256')

            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={'verify_exp': True}
            )

            # Add user info to request context
            request.user = payload

        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Token has expired'
            }), 401

        except jwt.InvalidTokenError as e:
            return jsonify({
                'error': 'Unauthorized',
                'message': f'Invalid token: {str(e)}'
            }), 401

        return f(*args, **kwargs)

    return decorated
```

**Usage in endpoints:**

```python
from app.middleware.sso_auth import require_sso_auth

@notes_bp.route('/', methods=['POST'])
@require_sso_auth  # Use SSO auth instead of API key
@notes_bp.arguments(NoteCreateSchema)
@notes_bp.response(201, NoteResponseSchema)
def create_note(note_data):
    # Access user info: request.user['username'], request.user['email']
    note = note_service.create_note(note_data)
    return note
```

**Environment variables:**

```env
# SSO Configuration
SSO_SECRET_KEY=your-shared-secret-with-sso
SSO_ALGORITHM=HS256
SSO_ISSUER=https://auth.your-domain.com
```

### Frontend Implementation

**File:** `frontend/src/lib/auth.ts`

```typescript
interface User {
  username: string;
  email: string;
  exp: number;
}

export const authService = {
  // Get token from localStorage
  getToken(): string | null {
    return localStorage.getItem('auth_token');
  },

  // Store token after SSO login
  setToken(token: string): void {
    localStorage.setItem('auth_token', token);
  },

  // Remove token on logout
  clearToken(): void {
    localStorage.removeItem('auth_token');
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    // Check if token is expired
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  },

  // Get user info from token
  getUser(): User | null {
    const token = this.getToken();
    if (!token) return null;

    try {
      return JSON.parse(atob(token.split('.')[1]));
    } catch {
      return null;
    }
  },

  // Redirect to SSO login
  login(): void {
    const ssoUrl = import.meta.env.VITE_SSO_URL;
    const callbackUrl = encodeURIComponent(window.location.origin + '/auth/callback');
    window.location.href = `${ssoUrl}/login?redirect=${callbackUrl}`;
  },

  // Handle SSO callback
  handleCallback(token: string): void {
    this.setToken(token);
    window.location.href = '/';
  },

  // Logout
  logout(): void {
    this.clearToken();
    const ssoUrl = import.meta.env.VITE_SSO_URL;
    window.location.href = `${ssoUrl}/logout`;
  },
};
```

**Update API client:**

```typescript
// frontend/src/lib/api.ts
import { authService } from './auth';

export const apiClient = {
  async createNote(data: NoteCreate) {
    const token = authService.getToken();

    const response = await fetch(`${API_BASE_URL}/notes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,  // Include JWT token
      },
      body: JSON.stringify(data),
    });

    if (response.status === 401) {
      // Token expired, redirect to login
      authService.login();
      throw new Error('Authentication required');
    }

    if (!response.ok) {
      throw new Error('Failed to create note');
    }

    return response.json();
  },
  // ... update all other methods similarly
};
```

**Add auth callback page:**

```typescript
// frontend/src/pages/AuthCallback.tsx
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '@/lib/auth';

export function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');

    if (token) {
      authService.setToken(token);
      navigate('/');
    } else {
      navigate('/login');
    }
  }, [searchParams, navigate]);

  return <div>Authenticating...</div>;
}
```

**Add route:**

```typescript
// frontend/src/App.tsx
import { AuthCallback } from './pages/AuthCallback';

<Routes>
  <Route path="/" element={<Index />} />
  <Route path="/auth/callback" element={<AuthCallback />} />
</Routes>
```

**Environment variables:**

```env
# frontend/.env
VITE_SSO_URL=https://auth.your-domain.com
VITE_API_BASE_URL=http://your-domain.com:5000/api
```

---

## Option 2: Authentik (Recommended)

Authentik is a powerful open-source SSO/Identity Provider with excellent features.

### Deployment

```yaml
# docker-compose.sso.yml
version: "3.9"

services:
  postgresql:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - database:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${PG_PASS}
      POSTGRES_USER: authentik
      POSTGRES_DB: authentik

  redis:
    image: redis:alpine
    restart: unless-stopped

  authentik-server:
    image: ghcr.io/goauthentik/server:latest
    restart: unless-stopped
    command: server
    environment:
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
      AUTHENTIK_POSTGRESQL__HOST: postgresql
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS}
      AUTHENTIK_REDIS__HOST: redis
    ports:
      - "9000:9000"
      - "9443:9443"
    depends_on:
      - postgresql
      - redis

  authentik-worker:
    image: ghcr.io/goauthentik/server:latest
    restart: unless-stopped
    command: worker
    environment:
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
      AUTHENTIK_POSTGRESQL__HOST: postgresql
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS}
      AUTHENTIK_REDIS__HOST: redis
    depends_on:
      - postgresql
      - redis

volumes:
  database:
```

### Configuration

1. **Access Authentik:** http://localhost:9000
2. **Initial setup:** Create admin user
3. **Create Application:**
   - Name: ADHD Printer
   - Slug: adhd-printer
   - Provider: OAuth2/OpenID

4. **Create Provider:**
   - Type: OAuth2/OpenID
   - Client Type: Public
   - Redirect URIs: http://your-domain.com/auth/callback
   - Signing Key: Generate new

5. **Get credentials:**
   - Client ID: (from provider)
   - Client Secret: (if using confidential)

### Backend with Authentik

**Install:**

```bash
pip install python-jose[cryptography] requests
```

**File:** `backend/app/middleware/authentik_auth.py`

```python
from functools import wraps
from flask import request, jsonify
import requests
from jose import jwt, JWTError
import os

AUTHENTIK_URL = os.getenv('AUTHENTIK_URL', 'http://authentik-server:9000')

def get_jwks():
    """Get public keys from Authentik"""
    response = requests.get(f'{AUTHENTIK_URL}/application/o/adhd-printer/jwks/')
    return response.json()

def require_authentik_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        try:
            # Verify token with Authentik's public keys
            jwks = get_jwks()
            payload = jwt.decode(
                token,
                jwks,
                audience='adhd-printer',
                issuer=f'{AUTHENTIK_URL}/application/o/adhd-printer/'
            )

            request.user = payload

        except JWTError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401

        return f(*args, **kwargs)

    return decorated
```

### Frontend with Authentik (OAuth2)

```typescript
// frontend/src/lib/authentik.ts
const AUTHENTIK_URL = import.meta.env.VITE_AUTHENTIK_URL;
const CLIENT_ID = import.meta.env.VITE_AUTHENTIK_CLIENT_ID;
const REDIRECT_URI = `${window.location.origin}/auth/callback`;

export const authentikService = {
  login() {
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      response_type: 'code',
      scope: 'openid profile email',
    });

    window.location.href = `${AUTHENTIK_URL}/application/o/authorize/?${params}`;
  },

  async handleCallback(code: string): Promise<string> {
    // Exchange code for token
    const response = await fetch(`${AUTHENTIK_URL}/application/o/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        client_id: CLIENT_ID,
        redirect_uri: REDIRECT_URI,
      }),
    });

    const data = await response.json();
    return data.access_token;
  },

  logout() {
    localStorage.removeItem('auth_token');
    window.location.href = `${AUTHENTIK_URL}/application/o/adhd-printer/end-session/`;
  },
};
```

---

## Option 3: Authelia (Lightweight)

Authelia is a lightweight authentication and authorization server.

### With Reverse Proxy

Authelia works best with a reverse proxy (nginx/Traefik):

```nginx
# nginx with Authelia
location / {
    auth_request /authelia;

    # Pass to backend if authenticated
    proxy_pass http://backend:5000;
}

location /authelia {
    internal;
    proxy_pass http://authelia:9091/api/verify;
}
```

This way, nginx handles auth before requests reach your API.

---

## Comparison

| Feature | API Keys | Pangolin | Authentik | Authelia |
|---------|----------|----------|-----------|----------|
| Complexity | ⭐ Simple | ⭐⭐ Medium | ⭐⭐⭐ Complex | ⭐⭐ Medium |
| User Management | ❌ No | ✅ Basic | ✅ Full | ✅ Full |
| Multi-factor Auth | ❌ No | ⚠️ Limited | ✅ Full | ✅ Full |
| OAuth2/OIDC | ❌ No | ⚠️ Limited | ✅ Full | ✅ Full |
| Session Management | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Resources | Very Light | Light | Medium | Light |
| Best For | Homelab | Small teams | Enterprise | Privacy-focused |

---

## Pros and Cons

### SSO Advantages

✅ **Pros:**
- Real user accounts
- Login/logout functionality
- Multi-factor authentication
- Session management
- Audit logging
- Password policies
- User self-service (password reset)
- Integration with LDAP/AD

### SSO Disadvantages

❌ **Cons:**
- More complex setup
- Additional service to maintain
- More resource usage
- Requires database
- Learning curve
- Token management in frontend

### API Keys Advantages

✅ **Pros:**
- Very simple to implement
- No extra services needed
- Stateless
- Fast
- Easy to rotate
- Works everywhere

### API Keys Disadvantages

❌ **Cons:**
- No user management
- No UI for users
- Manual key distribution
- No automatic expiry
- No MFA

---

## Recommendation

### For Homelab (Personal Use):
**Use API Keys** (simplest)
- 5 minutes to set up
- No extra services
- Good enough for personal use

### For Small Team (2-10 users):
**Use Authentik** (best balance)
- Full-featured
- Good UI
- OAuth2/OIDC standard
- Active development

### For Enterprise:
**Use Keycloak or Okta**
- Production-ready
- Industry standard
- Full compliance features

### For Maximum Privacy:
**Use Authelia**
- Self-hosted
- Privacy-focused
- Works with reverse proxy

---

## Implementation Checklist

### SSO Setup:
- [ ] Choose SSO solution
- [ ] Deploy SSO service
- [ ] Create application in SSO
- [ ] Get client credentials
- [ ] Configure redirect URIs

### Backend:
- [ ] Install JWT library
- [ ] Create auth decorator
- [ ] Add to endpoints
- [ ] Configure SSO URL and keys
- [ ] Test token validation

### Frontend:
- [ ] Create auth service
- [ ] Add login/logout UI
- [ ] Add callback handler
- [ ] Update API client with tokens
- [ ] Handle token expiry
- [ ] Add protected routes

### Testing:
- [ ] Test login flow
- [ ] Test API with valid token
- [ ] Test API without token
- [ ] Test token expiry
- [ ] Test logout

---

## Quick Answer

**Yes, SSO will work!** But:

1. **For simple homelab:** API keys are easier (see SECURITY_QUICKSTART.md)
2. **For proper user management:** SSO is better

The choice depends on:
- How many users?
- Need user accounts?
- Want MFA?
- Time to spend?

For just you and your partner: **API keys** = 5 minutes
For a team or public service: **SSO** = better long-term

Want help implementing either? Let me know which you prefer!
