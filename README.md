# TDAH Printer API

A REST API for generating and printing ADHD-focused reminder notes on USB thermal printers. Built with Flask following 12-factor app principles, designed to run in Docker with PostgreSQL.

## Features

- **REST API** for note generation and management
- **Template system** for customizable note designs
- **Thermal printer support** via USB (ESC/POS protocol)
- **HTML-to-PNG rendering** using Playwright/Chromium
- **PostgreSQL database** for note and template storage
- **Docker-ready** with USB passthrough support
- **OpenAPI/Swagger documentation** at `/swagger`
- **Comprehensive test suite** with pytest

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) USB thermal printer for physical printing

### 1. Clone and Setup

```bash
git clone <repository-url>
cd tdah-printer
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec api flask db upgrade

# Seed default template
docker-compose exec api flask seed-default-template
```

### 4. Access API

- API: http://localhost:5000/api/
- Swagger docs: http://localhost:5000/swagger
- Health check: http://localhost:5000/health/

## API Endpoints

### Notes

- `POST /api/notes/` - Create a new note
- `GET /api/notes/` - List notes (paginated)
- `GET /api/notes/{id}` - Get specific note
- `GET /api/notes/{id}/preview?format=html|image` - Preview note
- `POST /api/notes/{id}/print` - Print existing note

### Templates

- `POST /api/templates/` - Create a template
- `GET /api/templates/` - List all templates
- `GET /api/templates/{id}` - Get specific template
- `PUT /api/templates/{id}` - Update template

### Health

- `GET /health/` - Service health status

## Example Usage

### Create a Note

```bash
curl -X POST http://localhost:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "trabalho",
    "text": "Complete API documentation",
    "should_print": false
  }'
```

### List Notes

```bash
curl http://localhost:5000/api/notes/?page=1&per_page=20
```

### Preview Note

```bash
# HTML preview
curl http://localhost:5000/api/notes/1/preview?format=html

# Image preview
curl http://localhost:5000/api/notes/1/preview?format=image --output note.png
```

### Print a Note

```bash
curl -X POST http://localhost:5000/api/notes/1/print
```

## Development Setup

### Local Development (without Docker)

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Setup PostgreSQL (or use SQLite for dev)
# Update DATABASE_URL in .env

# Run migrations
flask db upgrade

# Seed default template
flask seed-default-template

# Run development server
flask run --debug
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_printer_service.py

# Run tests with real printer (hardware required)
pytest -m real_printer
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
ruff check app/ tests/

# Type checking
mypy app/
```

## USB Printer Configuration

### Finding USB Device Information

```bash
# Linux
lsusb
# Look for your printer, note vendor:product IDs

# macOS
system_profiler SPUSBDataType

# Windows
# Use Device Manager
```

### Docker USB Passthrough

Edit `docker-compose.yml`:

```yaml
api:
  devices:
    - /dev/bus/usb/001/002:/dev/bus/usb/001/002  # Adjust to your device
  privileged: true
  environment:
    - PRINTER_ENABLED=true
    - PRINTER_VENDOR_ID=0x6868
    - PRINTER_PRODUCT_ID=0x0200
```

### Proxmox USB Passthrough

1. Identify USB device on Proxmox host:
   ```bash
   lsusb
   ```

2. Add USB device to container in Proxmox UI:
   - Container → Hardware → Add → USB Device
   - Select your thermal printer

3. Update container environment variables in docker-compose or .env

## Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

## Environment Variables

See `.env.example` for all available configuration options:

- **Flask**: `FLASK_ENV`, `SECRET_KEY`, `DEBUG`
- **Database**: `DATABASE_URL`
- **Printer**: `PRINTER_*` settings
- **Application**: `UPLOAD_FOLDER`, pagination settings
- **API**: OpenAPI documentation settings
- **CORS**: `CORS_ORIGINS`

## Architecture

### 12-Factor App Compliance

1. **Codebase** - Single git repository
2. **Dependencies** - Explicit in pyproject.toml
3. **Config** - Environment variables
4. **Backing Services** - Postgres/printer as attached resources
5. **Build/Release/Run** - Docker multi-stage build
6. **Processes** - Stateless Flask app
7. **Port Binding** - Self-contained with Gunicorn
8. **Concurrency** - Horizontal scaling via Docker
9. **Disposability** - Fast startup, graceful shutdown
10. **Dev/Prod Parity** - Docker everywhere
11. **Logs** - Stdout (structured logging)
12. **Admin Processes** - Flask CLI commands

### Project Structure

```
tdah-printer/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Marshmallow schemas
│   ├── services/            # Business logic
│   ├── api/                 # REST endpoints
│   └── utils/               # Utilities & CLI
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # API integration tests
│   └── conftest.py         # Pytest fixtures
├── docker/
├── Dockerfile
├── docker-compose.yml
├── wsgi.py                  # WSGI entry point
└── pyproject.toml           # Dependencies & config
```

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `FLASK_ENV=production`
- [ ] Use strong database credentials
- [ ] Configure `CORS_ORIGINS` appropriately
- [ ] Enable HTTPS (use reverse proxy like nginx/traefik)
- [ ] Set up proper logging and monitoring
- [ ] Regular database backups
- [ ] Limit USB device access to necessary containers only

### Scaling

- Increase `--workers` in Gunicorn command (Dockerfile)
- Use Docker Swarm or Kubernetes for multi-instance deployment
- Add Redis for session storage if needed
- Use object storage (S3/MinIO) for uploads in multi-instance setups

## Troubleshooting

### Printer Not Working

- Check USB device passthrough configuration
- Verify `PRINTER_ENABLED=true`
- Confirm vendor/product IDs match your printer
- Check container logs: `docker-compose logs api`
- Test with mock printer first: `PRINTER_ENABLED=false`

### Database Connection Issues

- Ensure PostgreSQL is running: `docker-compose ps`
- Check `DATABASE_URL` format
- Wait for DB health check before starting API

### Playwright/Rendering Issues

- Ensure Chromium is installed: `playwright install chromium`
- Check system resources (memory/CPU)
- Review logs for specific Playwright errors

## License

[Your License Here]

## Contributing

[Contributing Guidelines]
