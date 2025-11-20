# Pangolin SSO Integration Guide

Pangolin is a lightweight SSO solution. This guide shows how to integrate it with your ADHD Printer API.

## Understanding Pangolin Keys

Pangolin uses:
1. **Signing Key** - Secret key to sign/verify JWT tokens (shared between Pangolin and your API)
2. **JWT Tokens** - Temporary tokens that users get after login
3. **Optional: API Keys** - For service-to-service or additional security

## Architecture

```
┌──────────────┐
│   User       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Frontend    │ (React app)
│              │
└──────┬───────┘
       │
       │ 1. Click login
       ▼
┌──────────────┐
│  Pangolin    │ (SSO service)
│  SSO         │ - Validates username/password
│              │ - Issues JWT token (signed with secret key)
└──────┬───────┘
       │
       │ 2. Return JWT token
       ▼
┌──────────────┐
│  Frontend    │ - Stores JWT in localStorage
│              │ - Includes JWT in all API requests
└──────┬───────┘
       │
       │ 3. API request with JWT
       ▼
┌──────────────┐
│  Backend     │ - Validates JWT signature
│  Flask API   │ - Checks expiry
│              │ - Extracts user info
└──────────────┘
```

---

## Option 1: Pangolin JWT Only (Recommended)

Use JWT tokens from Pangolin for all authentication.

### Backend Setup

**1. Install dependencies:**

```bash
# In backend directory
pip install PyJWT==2.8.0
```

**2. Update requirements.txt:**

```txt
# Add to backend/requirements.txt
PyJWT==2.8.0
```

**3. Create Pangolin auth middleware:**

**File:** `backend/app/middleware/pangolin_auth.py`

```python
"""
Pangolin SSO authentication using JWT tokens
"""
from functools import wraps
from flask import request, jsonify
import jwt
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def require_pangolin_auth(f):
    """
    Decorator to require valid Pangolin JWT token

    Token should be in Authorization header:
    Authorization: Bearer <jwt-token>

    Environment variables required:
    - PANGOLIN_SECRET_KEY: Shared secret with Pangolin
    - PANGOLIN_ALGORITHM: JWT algorithm (default: HS256)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            logger.warning(f"Missing token from {request.remote_addr}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication token required'
            }), 401

        try:
            # Get Pangolin configuration
            secret_key = os.getenv('PANGOLIN_SECRET_KEY')
            if not secret_key:
                logger.error("PANGOLIN_SECRET_KEY not configured!")
                return jsonify({
                    'error': 'Server configuration error',
                    'message': 'SSO not properly configured'
                }), 500

            algorithm = os.getenv('PANGOLIN_ALGORITHM', 'HS256')

            # Decode and verify JWT token
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
                options={
                    'verify_exp': True,  # Check expiration
                    'verify_iat': True,  # Check issued at
                }
            )

            # Optional: Verify issuer if Pangolin sets it
            issuer = os.getenv('PANGOLIN_ISSUER')
            if issuer and payload.get('iss') != issuer:
                raise jwt.InvalidIssuerError('Invalid token issuer')

            # Add user info to request context
            request.user = {
                'username': payload.get('sub') or payload.get('username'),
                'email': payload.get('email'),
                'name': payload.get('name'),
                'groups': payload.get('groups', []),
                'exp': payload.get('exp'),
            }

            logger.info(
                f"Authenticated user: {request.user['username']} from {request.remote_addr}"
            )

        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired token from {request.remote_addr}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Token has expired. Please login again.'
            }), 401

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token from {request.remote_addr}: {str(e)}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid authentication token'
            }), 401

        return f(*args, **kwargs)

    return decorated


def optional_pangolin_auth(f):
    """
    Optional authentication decorator
    Adds user info if token is present, but doesn't require it
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        request.user = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                secret_key = os.getenv('PANGOLIN_SECRET_KEY')
                algorithm = os.getenv('PANGOLIN_ALGORITHM', 'HS256')

                payload = jwt.decode(
                    token,
                    secret_key,
                    algorithms=[algorithm],
                    options={'verify_exp': True}
                )

                request.user = {
                    'username': payload.get('sub') or payload.get('username'),
                    'email': payload.get('email'),
                    'name': payload.get('name'),
                }
            except jwt.InvalidTokenError:
                pass  # Continue without user

        return f(*args, **kwargs)

    return decorated
```

**4. Update middleware __init__.py:**

```python
# backend/app/middleware/__init__.py
from .security import require_api_key, init_security
from .pangolin_auth import require_pangolin_auth, optional_pangolin_auth

__all__ = [
    'require_api_key',
    'init_security',
    'require_pangolin_auth',
    'optional_pangolin_auth',
]
```

**5. Protect your endpoints:**

```python
# backend/app/api/notes.py
from app.middleware import require_pangolin_auth

# Replace @require_api_key with @require_pangolin_auth

@notes_bp.route('/', methods=['POST'])
@require_pangolin_auth  # Use Pangolin auth
@notes_bp.arguments(NoteCreateSchema)
@notes_bp.response(201, NoteResponseSchema)
def create_note(note_data):
    """Create a new note"""
    # Access user info from request.user
    logger.info(f"Creating note for user: {request.user['username']}")

    note = note_service.create_note(note_data)
    return note


@notes_bp.route('/', methods=['GET'])
@optional_pangolin_auth  # Optional: works with or without auth
@notes_bp.arguments(NoteQuerySchema, location='query')
@notes_bp.response(200, PaginationSchema)
def list_notes(query_params):
    """List notes"""
    # If authenticated, could filter by user
    if request.user:
        logger.info(f"Listing notes for user: {request.user['username']}")

    notes = note_service.list_notes(**query_params)
    return notes
```

**6. Environment variables:**

```env
# backend/.env or in Portainer

# Pangolin SSO Configuration
PANGOLIN_SECRET_KEY=your-shared-secret-key-from-pangolin
PANGOLIN_ALGORITHM=HS256
PANGOLIN_ISSUER=https://pangolin.your-domain.com  # Optional

# CORS - allow your frontend
CORS_ORIGINS=http://your-domain.com:8080
```

---

### Frontend Setup

**1. Install dependencies:**

```bash
cd frontend
npm install jwt-decode
```

**2. Create auth service:**

**File:** `frontend/src/lib/pangolin-auth.ts`

```typescript
import { jwtDecode } from 'jwt-decode';

interface User {
  username: string;
  email?: string;
  name?: string;
  exp: number;
}

interface PangolinConfig {
  url: string;
  clientId: string;
}

const config: PangolinConfig = {
  url: import.meta.env.VITE_PANGOLIN_URL || 'http://localhost:8080',
  clientId: import.meta.env.VITE_PANGOLIN_CLIENT_ID || 'adhd-printer',
};

export const pangolinAuth = {
  /**
   * Get stored JWT token
   */
  getToken(): string | null {
    return localStorage.getItem('pangolin_token');
  },

  /**
   * Store JWT token
   */
  setToken(token: string): void {
    localStorage.setItem('pangolin_token', token);
  },

  /**
   * Clear stored token
   */
  clearToken(): void {
    localStorage.removeItem('pangolin_token');
  },

  /**
   * Check if user is authenticated and token is valid
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      const decoded = jwtDecode<User>(token);
      // Check if token is expired (with 60s buffer)
      return decoded.exp * 1000 > Date.now() + 60000;
    } catch {
      return false;
    }
  },

  /**
   * Get user information from token
   */
  getUser(): User | null {
    const token = this.getToken();
    if (!token) return null;

    try {
      return jwtDecode<User>(token);
    } catch {
      return null;
    }
  },

  /**
   * Redirect to Pangolin login
   */
  login(): void {
    // Save current URL to return after login
    sessionStorage.setItem('redirect_after_login', window.location.pathname);

    // Redirect to Pangolin
    const callbackUrl = encodeURIComponent(
      `${window.location.origin}/auth/callback`
    );

    window.location.href = `${config.url}/auth/login?client_id=${config.clientId}&redirect_uri=${callbackUrl}`;
  },

  /**
   * Handle callback from Pangolin
   */
  handleCallback(token: string): void {
    this.setToken(token);

    // Redirect to saved URL or home
    const redirectTo = sessionStorage.getItem('redirect_after_login') || '/';
    sessionStorage.removeItem('redirect_after_login');

    window.location.href = redirectTo;
  },

  /**
   * Logout
   */
  logout(): void {
    this.clearToken();

    // Redirect to Pangolin logout
    const callbackUrl = encodeURIComponent(window.location.origin);
    window.location.href = `${config.url}/auth/logout?redirect_uri=${callbackUrl}`;
  },
};
```

**3. Update API client to use JWT:**

**File:** `frontend/src/lib/api.ts`

```typescript
import { pangolinAuth } from './pangolin-auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = pangolinAuth.getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add JWT token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 401 - redirect to login
  if (response.status === 401) {
    pangolinAuth.login();
    throw new Error('Authentication required');
  }

  return response;
}

export const apiClient = {
  async createNote(data: NoteCreate) {
    const response = await fetchWithAuth(`${API_BASE_URL}/notes/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to create note');
    }

    return response.json();
  },

  async listNotes(params?: { page?: number; per_page?: number }) {
    const queryParams = new URLSearchParams(
      params as Record<string, string>
    ).toString();

    const response = await fetchWithAuth(
      `${API_BASE_URL}/notes/?${queryParams}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch notes');
    }

    return response.json();
  },

  // ... other methods using fetchWithAuth
};
```

**4. Create login page:**

**File:** `frontend/src/pages/Login.tsx`

```typescript
import { useEffect } from 'react';
import { pangolinAuth } from '@/lib/pangolin-auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function Login() {
  useEffect(() => {
    // If already authenticated, redirect to home
    if (pangolinAuth.isAuthenticated()) {
      window.location.href = '/';
    }
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-96">
        <CardHeader>
          <CardTitle>ADHD Printer</CardTitle>
          <CardDescription>
            Sign in to create and manage your reminder notes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={() => pangolinAuth.login()}
            className="w-full"
          >
            Sign in with SSO
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
```

**5. Create callback handler:**

**File:** `frontend/src/pages/AuthCallback.tsx`

```typescript
import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { pangolinAuth } from '@/lib/pangolin-auth';

export function AuthCallback() {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');

    if (error) {
      console.error('Auth error:', error);
      window.location.href = '/login?error=' + error;
      return;
    }

    if (token) {
      pangolinAuth.handleCallback(token);
    } else {
      window.location.href = '/login';
    }
  }, [searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p>Authenticating...</p>
    </div>
  );
}
```

**6. Add protected route wrapper:**

**File:** `frontend/src/components/ProtectedRoute.tsx`

```typescript
import { useEffect } from 'react';
import { pangolinAuth } from '@/lib/pangolin-auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  useEffect(() => {
    if (!pangolinAuth.isAuthenticated()) {
      pangolinAuth.login();
    }
  }, []);

  if (!pangolinAuth.isAuthenticated()) {
    return <div>Checking authentication...</div>;
  }

  return <>{children}</>;
}
```

**7. Update routes:**

```typescript
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { AuthCallback } from './pages/AuthCallback';
import { Index } from './pages/Index';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Index />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
```

**8. Environment variables:**

```env
# frontend/.env
VITE_PANGOLIN_URL=https://pangolin.your-domain.com
VITE_PANGOLIN_CLIENT_ID=adhd-printer
VITE_API_BASE_URL=http://your-domain.com:5000/api
```

---

## Option 2: Pangolin JWT + API Keys (Hybrid)

Use both SSO for user login AND API keys for service-to-service.

### When to use:
- Users login with Pangolin (JWT)
- Background services use API keys
- Mobile apps might use API keys

### Implementation:

**Backend - Accept both:**

```python
from app.middleware import require_pangolin_auth, require_api_key

def require_auth(f):
    """Accept either Pangolin JWT or API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for JWT token first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # Try Pangolin JWT
            return require_pangolin_auth(f)(*args, **kwargs)

        # Check for API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return require_api_key(f)(*args, **kwargs)

        return jsonify({'error': 'Authentication required'}), 401

    return decorated

# Use in endpoints
@notes_bp.route('/', methods=['POST'])
@require_auth  # Accepts JWT or API key
def create_note():
    pass
```

---

## Pangolin SSO Deployment

### With Docker Compose:

```yaml
# docker-compose.sso.yml
services:
  pangolin:
    image: pangolin/pangolin:latest  # Check actual image name
    container_name: pangolin-sso
    ports:
      - "8080:8080"
    environment:
      - PANGOLIN_SECRET_KEY=${PANGOLIN_SECRET_KEY}
      - PANGOLIN_ADMIN_PASSWORD=${ADMIN_PASSWORD}
    volumes:
      - pangolin_data:/data
    restart: unless-stopped

volumes:
  pangolin_data:
```

**Generate secret key:**

```bash
openssl rand -base64 32
```

---

## Configuration Checklist

### Pangolin SSO:
- [ ] Deploy Pangolin service
- [ ] Set PANGOLIN_SECRET_KEY (same in Pangolin and your API)
- [ ] Create application/client in Pangolin
- [ ] Configure redirect URIs
- [ ] Create test user

### Backend:
- [ ] Install PyJWT
- [ ] Create pangolin_auth.py middleware
- [ ] Add to middleware/__init__.py
- [ ] Replace @require_api_key with @require_pangolin_auth
- [ ] Set environment variables
- [ ] Test with sample JWT

### Frontend:
- [ ] Install jwt-decode
- [ ] Create pangolin-auth.ts
- [ ] Update api.ts to use JWT
- [ ] Create Login page
- [ ] Create AuthCallback page
- [ ] Add ProtectedRoute wrapper
- [ ] Update routes
- [ ] Set environment variables

### Testing:
- [ ] Can redirect to Pangolin login
- [ ] Can login successfully
- [ ] Token stored in localStorage
- [ ] API requests include JWT
- [ ] Backend validates JWT
- [ ] Can access protected routes
- [ ] Can logout
- [ ] Expired tokens redirect to login

---

## Summary

**Pangolin Secure Keys = JWT Tokens**

Pangolin uses a **shared secret key** to sign JWT tokens:
1. User logs in to Pangolin
2. Pangolin creates JWT signed with secret key
3. Frontend stores JWT
4. API validates JWT using same secret key

**Simple answer:** Yes, it works! The "secure key" is the `PANGOLIN_SECRET_KEY` that both Pangolin and your API share.

**Setup time:** ~30-60 minutes

Need help with any specific part?
