# Portainer Deployment Guide for ADHD Printer

This guide explains how to deploy your ADHD Printer application to Portainer in your homelab with the frontend public.

## Understanding the Architecture

Since your **frontend is a static site** (HTML/CSS/JS served by nginx), the JavaScript runs **in the user's browser**, not on your server. This means:

- `VITE_API_URL` must be accessible from wherever your users' browsers are
- If frontend is public, the API URL in `VITE_API_URL` must also be reachable publicly

## Two Deployment Options

### Option 1: Both Public (Simplest)

**Pros:**
- Simple to configure
- No reverse proxy needed
- Easy to debug

**Cons:**
- Backend API directly exposed to internet
- Need to secure both services
- Two different ports

**When to use:** Quick setup, trusted network, or behind a firewall

### Option 2: Reverse Proxy (Recommended)

**Pros:**
- ✅ Backend NOT directly exposed
- ✅ Single entry point (port 80/443)
- ✅ Better security
- ✅ Easy to add HTTPS later
- ✅ Clean URLs (no ports)

**Cons:**
- Slightly more complex setup
- One extra container (nginx)

**When to use:** Production, public internet, best practices

---

## Option 1: Both Public Deployment

### Step 1: Prepare Environment Variables

In Portainer, when creating the stack, set these environment variables:

```env
# Required
DATABASE_URL=postgresql://user:password@db-host/adhd_printer
SECRET_KEY=your-very-random-secret-key-change-this

# IMPORTANT: Replace with your actual domain or public IP
VITE_API_URL=http://your-domain.com:5000/api
# Or with IP: http://203.0.113.10:5000/api

# CORS - must include frontend URL
CORS_ORIGINS=http://your-domain.com:8080,https://your-domain.com

# Optional
PRINTER_ENABLED=true
MAX_THERMAL_WIDTH_PX=384
```

### Step 2: Deploy in Portainer

1. Go to **Stacks** → **Add Stack**
2. Name: `adhd-printer`
3. **Web editor** → Paste contents of `docker-compose.portainer-public.yml`
4. **Environment variables** → Add the variables above
5. **Deploy**

### Step 3: Configure Port Forwarding

If behind a router, forward these ports to your server:
- `5000` → Backend API
- `8080` → Frontend

### Step 4: Access

- Frontend: `http://your-domain.com:8080`
- Backend: `http://your-domain.com:5000/health/` (test)

---

## Option 2: Reverse Proxy Deployment (Recommended)

### Step 1: Prepare Environment Variables

In Portainer, when creating the stack:

```env
# Required
DATABASE_URL=postgresql://user:password@db-host/adhd_printer
SECRET_KEY=your-very-random-secret-key-change-this
DOMAIN=your-domain.com
# Or with IP: DOMAIN=203.0.113.10

# Optional
PRINTER_ENABLED=true
MAX_THERMAL_WIDTH_PX=384
```

**Note:** `VITE_API_URL` is NOT needed here! The frontend will be rebuilt to use `/api` (same domain).

### Step 2: Rebuild Frontend with Relative API URL

The frontend needs to be rebuilt with `VITE_API_URL=/api` so it calls the same domain.

**Option A: Use GitHub Actions** (automatic)
1. In your repository, update `.github/workflows/build-images.yml`
2. Change the frontend build args:
   ```yaml
   build-args: |
     VITE_API_URL=/api
   ```
3. Push to trigger rebuild

**Option B: Build locally**
```bash
docker build \
  --build-arg VITE_API_URL=/api \
  -t ghcr.io/mathbatistela/adhd-board-frontend:proxy \
  -f frontend/Dockerfile frontend/

docker push ghcr.io/mathbatistela/adhd-board-frontend:proxy
```

Then update the image tag in `docker-compose.portainer-proxy.yml`:
```yaml
frontend:
  image: ghcr.io/mathbatistela/adhd-board-frontend:proxy
```

### Step 3: Upload nginx Config

1. In Portainer, create a **Volume**: `adhd-nginx-config`
2. Upload `nginx-proxy.conf` to this volume
3. Or use bind mount: Map `./nginx-proxy.conf` from host

### Step 4: Deploy in Portainer

1. Go to **Stacks** → **Add Stack**
2. Name: `adhd-printer`
3. **Web editor** → Paste contents of `docker-compose.portainer-proxy.yml`
4. **Environment variables** → Add the variables above
5. **Deploy**

### Step 5: Configure Port Forwarding

Only forward **one port**:
- `80` (HTTP) → nginx proxy
- `443` (HTTPS) - optional, for SSL later

### Step 6: Access

- Everything: `http://your-domain.com`
- Frontend: `http://your-domain.com/`
- Backend: `http://your-domain.com/api/`
- Health: `http://your-domain.com/health/`

---

## Security Considerations

### For Both Options:

1. **Change SECRET_KEY:**
   ```bash
   # Generate random key
   openssl rand -hex 32
   ```

2. **Use HTTPS** (highly recommended for public deployments):
   - Set up Let's Encrypt with Certbot
   - Or use Cloudflare Tunnel
   - Or use Traefik with automatic HTTPS

3. **Firewall Rules:**
   - Only expose necessary ports
   - Use fail2ban for brute force protection

4. **Database Security:**
   - Don't expose PostgreSQL port publicly
   - Use strong passwords
   - Regular backups

### Option 1 Specific:

1. **CORS Configuration:**
   - Set `CORS_ORIGINS` to your actual domain
   - Don't use `*` in production

2. **API Rate Limiting:**
   - Consider adding nginx in front of API too
   - Or use Flask-Limiter

### Option 2 Specific:

1. **Nginx Security Headers:**
   Already configured in `nginx-proxy.conf`:
   - CORS headers
   - Request size limits
   - Timeouts

2. **Backend Isolation:**
   - Backend has no public ports
   - Only accessible through nginx

---

## Troubleshooting

### Frontend can't reach backend

**Symptom:** Console errors like "Failed to fetch" or CORS errors

**Option 1 Fix:**
1. Check `VITE_API_URL` is set to your **public** domain/IP
2. Verify port forwarding is working
3. Check `CORS_ORIGINS` includes frontend URL

**Option 2 Fix:**
1. Check nginx logs: `docker logs adhd-board-proxy`
2. Verify nginx config is loaded
3. Test API directly: `curl http://localhost/api/health/`

### CORS Errors

**Symptoms:** Browser console shows CORS policy errors

**Fix:**
```bash
# Check backend CORS settings
docker exec adhd-board-api env | grep CORS

# Should output your frontend URL
# For Option 1: CORS_ORIGINS=http://your-domain.com:8080
# For Option 2: CORS_ORIGINS=http://your-domain.com
```

### Printer Not Working

**Symptom:** Notes created but not printing

**Fix:**
1. Check USB device is mapped:
   ```bash
   docker exec adhd-board-api ls -la /dev/bus/usb/
   ```

2. Check printer permissions:
   ```bash
   # On host, find lp group GID
   getent group lp
   # Update docker-compose group_add with correct GID
   ```

### Can't Access from Internet

**Symptom:** Works on local network but not from outside

**Fix:**
1. Check port forwarding on router
2. Verify public IP: `curl ifconfig.me`
3. Check firewall rules: `sudo ufw status`
4. Test from outside: Use your phone's mobile data

---

## Adding HTTPS (Optional but Recommended)

### With Let's Encrypt:

1. Install Certbot on host:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. Get certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. Update docker-compose to expose port 443

### With Cloudflare Tunnel (Easiest):

1. Sign up for Cloudflare (free)
2. Add your domain
3. Install cloudflared in a container
4. No port forwarding needed!
5. Automatic HTTPS

---

## Database Setup

If you don't have PostgreSQL yet:

```yaml
# Add to docker-compose
services:
  db:
    image: postgres:15-alpine
    container_name: adhd-board-db
    environment:
      POSTGRES_DB: adhd_printer
      POSTGRES_USER: adhd_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - internal

volumes:
  postgres_data:
```

Then set:
```env
DATABASE_URL=postgresql://adhd_user:${DB_PASSWORD}@db:5432/adhd_printer
```

---

## Monitoring

View logs in Portainer:
1. Go to **Containers**
2. Click container name
3. **Logs** tab

Or via CLI:
```bash
docker logs -f adhd-board-api
docker logs -f adhd-board-frontend
docker logs -f adhd-board-proxy  # Option 2 only
```

---

## Summary

**For quick setup:** Use Option 1
**For production:** Use Option 2

Both options work, but Option 2 is more secure and professional. The key difference is whether your backend API is directly exposed to the internet or hidden behind a reverse proxy.

Need help? Check the logs and troubleshooting section above!
