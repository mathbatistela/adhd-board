# Deployment Guide: ADHD Board API to Homelab

This guide explains how to deploy the ADHD Board API to your homelab using GitHub Container Registry (GHCR) and Portainer.

## Architecture Overview

- **Image Registry**: GitHub Container Registry (GHCR)
- **CI/CD**: GitHub Actions (automatic builds on push to master)
- **Container Orchestration**: Portainer
- **Database**: External PostgreSQL server (already running on your homelab)
- **Hardware**: USB thermal printer passthrough

## Prerequisites

- [ ] GitHub repository with Actions enabled
- [ ] Portainer installed on your homelab
- [ ] PostgreSQL database running and accessible (yours: `192.168.237.103:5432`)
- [ ] USB thermal printer connected to the host machine
- [ ] Docker installed on the host machine

## Step 1: Set Up GitHub Container Registry

### 1.1 Configure Repository Settings

1. Go to your GitHub repository
2. Navigate to **Settings** → **Actions** → **General**
3. Under "Workflow permissions", ensure:
   - "Read and write permissions" is selected
   - "Allow GitHub Actions to create and approve pull requests" is checked

### 1.2 Make Package Public (Optional but Recommended)

After the first build:

1. Go to your GitHub profile → **Packages**
2. Find `tdah-printer` package
3. Click **Package settings**
4. Under "Danger Zone" → **Change visibility** → **Public**
5. This allows pulling the image without authentication

## Step 2: Trigger First Build

The GitHub Actions workflow (`.github/workflows/docker-publish.yml`) will automatically build and push images when you push to the `main` branch.

### Option A: Push to Main

```bash
# Add and commit the workflow file
git add .github/workflows/docker-publish.yml docker-compose.portainer.yml DEPLOYMENT.md
git commit -m "Add GHCR deployment workflow and Portainer stack"
git push origin main
```

### Option B: Manual Trigger

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select "Build and Push to GHCR" workflow
4. Click **Run workflow** → **Run workflow**

### Verify the Build

1. Go to **Actions** tab and monitor the workflow progress
2. Once complete, go to your profile → **Packages**
3. You should see `adhd-board` package with tag `latest`

The image URL will be: `ghcr.io/YOUR_GITHUB_USERNAME/adhd-board:latest`

## Step 3: Configure Portainer Stack

### 3.1 Find Your USB Printer Device

On your homelab host machine:

```bash
# List USB devices
lsusb

# Example output:
# Bus 001 Device 012: ID 6868:0200 Thermal Printer

# Note the Bus and Device number (e.g., 001/012)
# The device path will be: /dev/bus/usb/001/012
```

### 3.2 Update docker-compose.portainer.yml

Edit `docker-compose.portainer.yml` and update:

1. Replace `${GITHUB_USER}` with your GitHub username in the image line
2. Update the USB device path to match your printer:
   ```yaml
   devices:
     - /dev/bus/usb/001/012:/dev/bus/usb/001/012  # Update 001/012
   ```

### 3.3 Create Stack in Portainer

1. Log in to your Portainer instance
2. Select your environment (e.g., local Docker)
3. Navigate to **Stacks** → **Add stack**
4. Give it a name: `adhd-board`
5. Choose **Git Repository** or **Upload** method:

#### Option A: Git Repository (Recommended)

- **Repository URL**: `https://github.com/YOUR_USERNAME/adhd-board`
- **Repository reference**: `refs/heads/main`
- **Compose path**: `docker-compose.portainer.yml`

#### Option B: Web editor

- Copy and paste the contents of `docker-compose.portainer.yml`

### 3.4 Configure Environment Variables

In Portainer, under "Environment variables", add:

```env
# Required
GITHUB_USER=your-github-username
DATABASE_URL=postgresql://adhd_board_user:UgMKjstA0X4S7B2v7zF3@192.168.237.103:5432/adhd_board_database
SECRET_KEY=your-super-secret-random-key-here

# Printer Configuration (adjust if needed)
PRINTER_ENABLED=true
PRINTER_VENDOR_ID=26728
PRINTER_PRODUCT_ID=512
PRINTER_INTERFACE=0
PRINTER_IN_ENDPOINT=129
PRINTER_OUT_ENDPOINT=3

# Optional (defaults are usually fine)
FLASK_ENV=production
MAX_THERMAL_WIDTH_PX=384
THERMAL_DPI=203
API_TITLE=ADHD Board API
CORS_ORIGINS=*
```

**Important**: Generate a strong `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.5 Deploy the Stack

1. Click **Deploy the stack**
2. Wait for the container to pull the image and start
3. Check the logs for any errors

## Step 4: Verify Deployment

### 4.1 Check Container Status

In Portainer:
- Go to **Containers**
- Find `adhd-board-api`
- Status should be "running" with a green indicator

### 4.2 Check Health

```bash
# From your homelab host or another machine
curl http://YOUR_HOST_IP:5000/health/

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "printer": "connected"  # or "mock" if PRINTER_ENABLED=false
# }
```

### 4.3 Access API Documentation

Open in your browser:
```
http://YOUR_HOST_IP:5000/swagger
```

You should see the Swagger UI with all API endpoints.

### 4.4 Test Creating a Note

```bash
curl -X POST http://YOUR_HOST_IP:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "trabalho",
    "text": "Test note from deployment"
  }'
```

## Step 5: Automatic Updates

### 5.1 How It Works

Every time you push to the `main` branch:
1. GitHub Actions builds a new Docker image
2. Pushes it to GHCR with the `latest` tag
3. You can then update the container in Portainer

### 5.2 Update Container in Portainer

**Option A: Recreate Stack**
1. Go to **Stacks** → `adhd-board`
2. Click **Update the stack**
3. Enable "Re-pull image and redeploy"
4. Click **Update**

**Option B: Pull and Recreate Container**
1. Go to **Containers** → `adhd-board-api`
2. Click **Recreate**
3. Enable "Pull latest image"
4. Click **Recreate**

### 5.3 Webhook for Auto-Updates (Advanced)

Configure a webhook in Portainer to automatically update when a new image is pushed:

1. In Portainer, go to **Stacks** → `adhd-board` → **Webhooks**
2. Create a new webhook
3. Add the webhook URL to your GitHub repository:
   - **Settings** → **Webhooks** → **Add webhook**
   - Payload URL: Your Portainer webhook URL
   - Content type: `application/json`
   - Trigger: Just the push event

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs adhd-board-api
```

**Common issues:**
- Database connection failed → Verify `DATABASE_URL` is correct
- Printer not found → Check USB device path and `lsusb` output
- Permission denied → Ensure container is running as root (`user: "0"`)

### Database Connection Issues

```bash
# Test database connection from host
psql postgresql://adhd_board_user:UgMKjstA0X4S7B2v7zF3@192.168.237.103:5432/adhd_board_database

# If connection times out, check:
# - PostgreSQL is running
# - Firewall allows connections from Docker network
# - PostgreSQL pg_hba.conf allows connections from Docker IP
```

### Printer Not Detected

```bash
# On the host machine
lsusb                    # Verify printer is connected
ls -l /dev/bus/usb/001/  # Check device permissions

# Grant permissions (if needed)
sudo chmod 666 /dev/bus/usb/001/012
```

### Image Pull Failed

**If package is private:**
1. Create GitHub Personal Access Token (PAT):
   - **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Scopes: `read:packages`
2. In Portainer:
   - **Registries** → **Add registry**
   - Type: Custom
   - Registry URL: `ghcr.io`
   - Username: Your GitHub username
   - Password: Your PAT

## LXC Container Notes (Proxmox)

If running Docker in an LXC container on Proxmox:

### USB Passthrough

1. Find USB device on Proxmox host:
   ```bash
   lsusb
   # Note: Bus 001 Device 012: ID 6868:0200
   ```

2. Edit LXC container config (`/etc/pve/lxc/<CTID>.conf`):
   ```
   lxc.cgroup2.devices.allow: c 189:* rwm
   lxc.mount.entry: /dev/bus/usb/001 dev/bus/usb/001 none bind,optional,create=dir
   ```

3. Restart LXC container

### Privileged Container

For USB access, the LXC container should be privileged:
```
# In container config
unprivileged: 0
```

## Backup and Restore

### Backup Uploaded Images

```bash
# Create backup of uploads volume
docker run --rm -v adhd-board_adhd_board_uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Uploaded Images

```bash
# Restore from backup
docker run --rm -v adhd-board_adhd_board_uploads:/data -v $(pwd):/backup \
  alpine tar xzf /backup/uploads-backup-YYYYMMDD.tar.gz -C /
```

## Monitoring

### Healthcheck

The container includes a healthcheck that runs every 30 seconds:
```bash
# Manual healthcheck
docker exec adhd-board-api python -c "import requests; requests.get('http://localhost:5000/health/')"
```

### Logs

```bash
# Follow logs in real-time
docker logs -f adhd-board-api

# Last 100 lines
docker logs --tail 100 adhd-board-api
```

## Security Considerations

1. **SECRET_KEY**: Use a cryptographically secure random string
2. **Database Password**: Use a strong password (you already have a good one)
3. **CORS**: In production, set specific origins instead of `*`
4. **Firewall**: Restrict access to port 5000 to your local network only
5. **HTTPS**: Consider putting the API behind a reverse proxy (Nginx, Traefik) with SSL

## Support

For issues:
- Check logs: `docker logs adhd-board-api`
- Verify environment variables in Portainer
- Test database connectivity
- Check USB device permissions
