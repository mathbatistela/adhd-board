# ADHD Printer Frontend - Lovable Integration

This frontend is generated and managed by [Lovable](https://lovable.dev) and synced from the repository:
`git@github.com:mathbatistela/quick-receipt-notes.git`

## Technology Stack

The frontend is built with:

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite 5** - Build tool and dev server
- **Tailwind CSS 3** - Utility-first CSS framework
- **shadcn/ui** - Re-usable component library (Radix UI + Tailwind)
- **React Router 6** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **React Hook Form + Zod** - Form handling and validation
- **date-fns** - Date manipulation
- **Lucide React** - Icon library

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ui/          # shadcn/ui components
│   ├── lib/
│   │   ├── api.ts       # API client configuration
│   │   ├── storage.ts   # Local storage utilities
│   │   └── utils.ts     # Utility functions
│   ├── pages/           # Route components
│   ├── hooks/           # Custom React hooks
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles (Tailwind)
├── public/              # Static assets
├── package.json         # Dependencies
├── vite.config.ts       # Vite configuration
├── tailwind.config.ts   # Tailwind configuration
├── tsconfig.json        # TypeScript configuration
└── Dockerfile.new       # Production Docker build
```

## Development Workflow

### Initial Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env to set VITE_API_URL
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:5173`

### Working with Lovable

#### Updating from Lovable Repository

When Lovable generates new code or you make changes in the Lovable editor:

1. **Run the update script from the project root:**
   ```bash
   cd /path/to/tdah-printer
   ./update-frontend.sh
   ```

   This script will:
   - Pull the latest code from `quick-receipt-notes` repository
   - Sync all files to the `frontend/` directory
   - Preserve your local `.env` files
   - Exclude `node_modules`, `dist`, and Docker-related files

2. **Review the changes:**
   ```bash
   cd frontend
   git diff
   ```

3. **Install any new dependencies:**
   ```bash
   npm install
   ```

4. **Test locally:**
   ```bash
   npm run dev
   ```

5. **Commit the changes to this repository if needed**

#### Manual Sync (Alternative)

If you prefer manual control:

```bash
cd /tmp
git clone git@github.com:mathbatistela/quick-receipt-notes.git
rsync -av --exclude='node_modules' --exclude='.git' \
  /tmp/quick-receipt-notes/ ./frontend/
```

### API Integration

The frontend expects the backend API to be available at the URL specified in `VITE_API_URL`.

**Development:**
```env
VITE_API_URL=http://localhost:5000/api
```

**Production (Docker):**
```env
VITE_API_URL=http://api:5000/api
```

API client is configured in `src/lib/api.ts`.

## Building for Production

### Local Build

```bash
npm run build
```

Output will be in `dist/` directory.

### Docker Build

The new Dockerfile (`Dockerfile.new`) uses a multi-stage build:

**Stage 1 (builder):** Installs dependencies and builds the app
**Stage 2 (production):** Serves static files with Nginx

**Build the image:**
```bash
docker build -f Dockerfile.new -t adhd-printer-frontend \
  --build-arg VITE_API_URL=http://api:5000/api .
```

**Run the container:**
```bash
docker run -p 8080:80 adhd-printer-frontend
```

### Docker Compose

Update `docker-compose.yml` to use the new Dockerfile:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.new
    args:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:5000/api}
  container_name: adhd-board-frontend
  depends_on:
    - api
  ports:
    - "4173:80"
  restart: unless-stopped
```

Then rebuild:
```bash
docker-compose build frontend
docker-compose up -d frontend
```

## Common Tasks

### Adding shadcn/ui Components

Lovable manages components, but if you need to add new ones manually:

```bash
npx shadcn@latest add button
npx shadcn@latest add dialog
# etc.
```

Components will be added to `src/components/ui/`

### Updating Dependencies

```bash
# Check for updates
npm outdated

# Update all dependencies
npm update

# Update specific package
npm install react@latest
```

### Linting and Formatting

```bash
# Run ESLint
npm run lint

# Type checking
npx tsc --noEmit
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:5000/api` |

Vite exposes env vars prefixed with `VITE_` to the client code. Access them via:

```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Troubleshooting

### Port Already in Use

If port 5173 is already taken:
```bash
npm run dev -- --port 3000
```

### Build Fails

1. Clear cache and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Check Node version (requires Node 18+):
   ```bash
   node --version
   ```

### Docker Build Fails

1. Check Docker build context size:
   ```bash
   du -sh frontend/
   ```

2. Ensure `.dockerignore` excludes `node_modules` and `dist`

3. Try building with no cache:
   ```bash
   docker-compose build --no-cache frontend
   ```

### CORS Issues

If you see CORS errors in the browser console:

1. Check that `VITE_API_URL` points to the correct backend
2. Ensure backend `CORS_ORIGINS` includes the frontend URL
3. In development, Vite proxy can help (see `vite.config.ts`)

## File Organization Rules

### DO NOT COMMIT:
- `node_modules/` - Always gitignored
- `dist/` or `build/` - Build artifacts
- `.env` or `.env.local` - Local configuration
- `*.log` - Log files

### DO COMMIT:
- All source code in `src/`
- Configuration files (`package.json`, `vite.config.ts`, etc.)
- `.env.example` - Template for environment variables
- `public/` assets

### PRESERVE LOCALLY:
- `.env` - Your local environment config
- `Dockerfile.new` - Custom Dockerfile for this project
- `.dockerignore` - Docker build exclusions
- This `README.lovable.md` - Documentation

The `update-frontend.sh` script is configured to preserve these files during sync.

## Resources

- [Lovable Documentation](https://docs.lovable.dev)
- [Vite Documentation](https://vitejs.dev)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [React Documentation](https://react.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [TanStack Query Documentation](https://tanstack.com/query/latest)

## Notes

- The original simple frontend is preserved as `Dockerfile` (the old version)
- The new Lovable-based frontend uses `Dockerfile.new`
- To switch between them, update the `dockerfile` field in `docker-compose.yml`
- The Lovable repository may have its own Dockerfile - we maintain our own for consistency with the project structure
