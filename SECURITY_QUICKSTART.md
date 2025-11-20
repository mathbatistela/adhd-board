# Security Quick Start Guide

This is a **5-minute guide** to add basic security to your API.

## What You Get

After following this guide:
- ✅ API key authentication
- ✅ Request logging
- ✅ Security headers
- ✅ Optional IP whitelist

## Step 1: Generate API Keys (2 minutes)

```bash
# Generate a strong API key
openssl rand -hex 32
```

Copy the output. You'll need it.

## Step 2: Update Backend (1 minute)

**File:** `backend/app/__init__.py`

Add these lines:

```python
# At the top with other imports
from app.middleware import init_security, require_api_key

# Inside create_app(), after app = Flask(__name__)
def create_app(config_class=Config):
    app = Flask(__name__)

    # ... existing config ...

    # ADD THIS LINE (after config, before blueprints)
    init_security(app)

    # ... rest of code ...
```

**File:** `backend/app/api/notes.py`

Protect your endpoints:

```python
# At the top with other imports
from app.middleware import require_api_key

# Add decorator to POST/PUT/DELETE endpoints
@notes_bp.route('/', methods=['POST'])
@require_api_key  # ADD THIS LINE
@notes_bp.arguments(NoteCreateSchema)
@notes_bp.response(201, NoteResponseSchema)
def create_note(note_data):
    # ... existing code ...

@notes_bp.route('/<int:note_id>', methods=['PUT'])
@require_api_key  # ADD THIS LINE
# ... existing code ...

@notes_bp.route('/<int:note_id>/print', methods=['POST'])
@require_api_key  # ADD THIS LINE
# ... existing code ...
```

## Step 3: Configure Environment (1 minute)

**File:** `backend/.env` or set in Portainer

```env
# Add your generated API key(s)
API_KEYS=your-key-from-step-1

# Specific CORS origins (replace with your domain)
CORS_ORIGINS=http://your-domain.com:8080,https://your-domain.com

# Optional: Whitelist specific IPs (leave empty to allow all)
# ALLOWED_IPS=192.168.1.100,203.0.113.10
```

## Step 4: Update Frontend (1 minute)

**File:** `frontend/.env`

```env
# Add your API key
VITE_API_KEY=your-key-from-step-1

# Your API URL
VITE_API_BASE_URL=http://your-domain.com:5000/api
```

**File:** `frontend/src/lib/api.ts`

Update all API calls to include the key:

```typescript
const API_KEY = import.meta.env.VITE_API_KEY;

export const createNote = async (data: NoteCreate) => {
  const response = await fetch(`${API_BASE_URL}/notes/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,  // ADD THIS LINE to all requests
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create note');
  }

  return response.json();
};

// Repeat for all API functions: updateNote, deleteNote, printNote, etc.
```

## Step 5: Restart & Test

```bash
# Restart backend
docker-compose restart api

# Or rebuild if using Portainer
# Stack → adhd-printer → Stop → Start

# Test WITHOUT API key (should fail with 401)
curl -X POST http://localhost:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{"category": "trabalho", "text": "test"}'

# Expected: {"error": "Unauthorized", "message": "API key required..."}

# Test WITH API key (should work)
curl -X POST http://localhost:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"category": "trabalho", "text": "test note"}'

# Expected: {"id": 1, "category": "trabalho", ...}
```

## Done! 🎉

Your API is now protected with:
- ✅ Authentication via API keys
- ✅ Request logging to `/app/logs/security.log`
- ✅ Security headers on all responses
- ✅ Optional IP whitelisting

## View Logs

```bash
# In Docker container
docker exec adhd-board-api cat /app/logs/security.log

# In Portainer
Containers → adhd-board-api → Exec console
cat /app/logs/security.log
```

## Troubleshooting

### Frontend can't connect

**Check:** Is VITE_API_KEY set correctly?

```bash
# In frontend container or local dev
echo $VITE_API_KEY
# Should output your key
```

**Fix:** Rebuild frontend with correct env var

```bash
docker-compose build frontend
# or
npm run build  # if running locally
```

### 401 Unauthorized

**Check:** Is API_KEYS set in backend?

```bash
docker exec adhd-board-api env | grep API_KEYS
# Should output: API_KEYS=your-key
```

**Fix:** Set in docker-compose or .env, then restart

### CORS errors

**Check:** CORS_ORIGINS includes your frontend URL

```bash
docker exec adhd-board-api env | grep CORS_ORIGINS
```

**Fix:** Update CORS_ORIGINS to include your domain

## Next Steps (Optional)

For more security, see `API_SECURITY.md`:

1. **Rate Limiting** - Prevent abuse
2. **HTTPS** - Encrypt traffic
3. **Reverse Proxy** - Hide backend
4. **IP Whitelist** - Restrict access
5. **Fail2ban** - Block attackers
6. **Monitoring** - Alert on suspicious activity

## Security Checklist

- [ ] Generated strong API key
- [ ] Added `init_security(app)` to backend
- [ ] Added `@require_api_key` to endpoints
- [ ] Set `API_KEYS` environment variable
- [ ] Set `CORS_ORIGINS` (not `*`)
- [ ] Added `VITE_API_KEY` to frontend
- [ ] Updated frontend API calls with key
- [ ] Tested without key (should fail)
- [ ] Tested with key (should work)
- [ ] Can view security logs

## Managing API Keys

### Add Multiple Keys

```env
API_KEYS=key-for-web,key-for-mobile,key-for-admin
```

### Rotate Keys

1. Generate new key
2. Add to API_KEYS: `old-key,new-key`
3. Update frontend to use new key
4. Test everything works
5. Remove old key from API_KEYS

### Revoke Access

Remove the key from API_KEYS and restart.

## Questions?

See `API_SECURITY.md` for comprehensive guide.
