# Lovable Frontend Integration Setup

This document explains how the ADHD Printer project integrates with the Lovable-generated frontend.

## Overview

The frontend for this project is now being developed using [Lovable](https://lovable.dev), a visual development platform. The code is maintained in a separate repository and synced to this project using an automated script.

**Lovable Repository:** `git@github.com:mathbatistela/quick-receipt-notes.git`
**Main Project:** This repository (tdah-printer)

## Files Added

### Root Directory

- **`update-frontend.sh`** (gitignored) - Automated sync script that pulls updates from the Lovable repository
- **`LOVABLE_SETUP.md`** (this file) - Documentation for the Lovable integration

### Frontend Directory

- **`Dockerfile.new`** - Modern multi-stage Dockerfile for the Lovable frontend (React + TypeScript + Vite)
- **`.dockerignore`** - Optimized Docker build exclusions
- **`.env.example`** - Environment variable template
- **`README.lovable.md`** - Comprehensive frontend documentation

The script also synced the complete Lovable-generated React application with all its dependencies and components.

## Quick Start

### 1. Sync Latest Frontend Code

From the project root:

```bash
./update-frontend.sh
```

This will:
- Pull the latest code from the Lovable repository
- Sync all files to `frontend/` directory
- Preserve local configurations (`.env` files, Dockerfiles, etc.)

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Build for Production (Docker)

```bash
# Build using the new Dockerfile
docker build -f frontend/Dockerfile.new -t adhd-printer-frontend \
  --build-arg VITE_API_URL=http://api:5000/api frontend/

# Or update docker-compose.yml and rebuild
docker-compose build frontend
docker-compose up -d
```

## Architecture

### Technology Stack

The Lovable frontend is built with modern tools:

- **React 18** with **TypeScript** for type-safe UI development
- **Vite 5** for fast builds and hot module replacement
- **Tailwind CSS 3** for utility-first styling
- **shadcn/ui** for beautiful, accessible components (built on Radix UI)
- **TanStack Query** for server state management
- **React Hook Form + Zod** for form validation
- **React Router 6** for client-side routing

### Integration Points

1. **Backend API:** The frontend connects to the Flask API via `VITE_API_URL`
2. **Docker Compose:** Both frontend and backend run as separate services
3. **Development:** Frontend can be developed independently using Vite dev server

## Workflow

### Development Cycle

1. **Make changes in Lovable** - Use the Lovable visual editor to modify the frontend
2. **Sync changes** - Run `./update-frontend.sh` to pull updates
3. **Test locally** - Run `npm run dev` to test changes
4. **Commit** - Commit the synced changes to this repository
5. **Deploy** - Rebuild Docker images for production

### File Management

The update script is configured to:

**SYNC from Lovable:**
- All source code (`src/`)
- Configuration files (`vite.config.ts`, `tsconfig.json`, etc.)
- Package definitions (`package.json`, `package-lock.json`)
- Public assets (`public/`)

**PRESERVE locally:**
- `.env` and `.env.local` (environment config)
- `Dockerfile.new` (our custom Docker build)
- `.dockerignore` (Docker build optimizations)
- `README.lovable.md` (our documentation)

## Configuration

### Environment Variables

Create `frontend/.env` with:

```env
# Development
VITE_API_URL=http://localhost:5000/api

# Production (Docker)
# VITE_API_URL=http://api:5000/api
```

### Docker Setup

To use the new Lovable frontend in production:

1. Update `docker-compose.yml`:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.new  # Changed from Dockerfile
    args:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:5000/api}
  # ... rest of config
```

2. Rebuild:

```bash
docker-compose build frontend
docker-compose up -d
```

## Maintenance

### Updating Dependencies

After syncing from Lovable:

```bash
cd frontend
npm install  # Install new dependencies
npm audit    # Check for security issues
npm update   # Update to latest compatible versions
```

### Troubleshooting

**Problem:** Update script fails with "Permission denied"
```bash
chmod +x update-frontend.sh
```

**Problem:** Port 5173 already in use
```bash
npm run dev -- --port 3000
```

**Problem:** Docker build fails
```bash
# Clear Docker cache and rebuild
docker-compose build --no-cache frontend
```

**Problem:** CORS errors in browser
- Check `VITE_API_URL` points to correct backend
- Ensure backend has `CORS_ORIGINS=*` or includes frontend URL

## Migration Notes

### Old Frontend vs New Frontend

**Old Frontend (Dockerfile):**
- Simple React application
- Minimal dependencies
- Basic styling

**New Frontend (Dockerfile.new):**
- Full TypeScript support
- shadcn/ui component library
- Advanced state management
- Better developer experience

Both Dockerfiles are preserved. Switch between them by changing the `dockerfile` field in `docker-compose.yml`.

## Security Considerations

1. **Environment Variables:** Never commit `.env` files - they're in `.gitignore`
2. **API Keys:** Store sensitive keys only in `.env.local` (also gitignored)
3. **Update Script:** The script is gitignored to prevent accidental commits with custom modifications
4. **Dependencies:** Regularly update npm packages for security patches

## Resources

- [Lovable Documentation](https://docs.lovable.dev)
- [Frontend README](./frontend/README.lovable.md) - Detailed frontend docs
- [Update Script](./update-frontend.sh) - Automated sync tool
- [Lovable Repository](https://github.com/mathbatistela/quick-receipt-notes) - Source of truth for frontend code

## Support

For questions about:
- **Lovable platform:** See [Lovable docs](https://docs.lovable.dev)
- **Frontend development:** See `frontend/README.lovable.md`
- **Integration setup:** Review this document
- **Backend API:** See main `CLAUDE.md` and backend docs

## Future Improvements

- [ ] Automate the update script via GitHub Actions
- [ ] Add pre-commit hooks to ensure frontend is synced
- [ ] Set up automated testing for frontend
- [ ] Configure CI/CD pipeline for automatic deployments
- [ ] Add Storybook for component documentation
