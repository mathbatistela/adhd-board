# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**adhd Printer API** is a Flask REST API for generating and printing ADHD-focused reminder notes on USB thermal printers. The application follows 12-factor app principles and is designed to run in Docker with PostgreSQL for data persistence.

### Core Components

1. **REST API** (`app/api/`) - Flask-Smorest endpoints for notes and templates
2. **Note Renderer Service** (`app/services/note_renderer.py`) - Playwright-based HTML-to-PNG conversion
3. **Printer Service** (`app/services/printer.py`) - ESC/POS thermal printer abstraction
4. **Database Models** (`app/models/`) - SQLAlchemy models for notes and templates
5. **HTML Templates** (`app/templates/`) - Note rendering templates

## Architecture

### Service-Oriented Design

The application uses dependency injection and service abstraction for testability:

- **`NoteService`** (`app/services/note_service.py`) - High-level note CRUD operations, coordinates rendering and printing
- **`NoteRendererService`** (`app/services/note_renderer.py`) - HTML template processing and Playwright rendering
- **`PrinterService`** (`app/services/printer.py`) - USB thermal printer communication via python-escpos
- **`TemplateService`** (`app/services/template_service.py`) - Template management and retrieval

### API Layer

Flask-Smorest blueprints with automatic OpenAPI documentation:

- **`notes_bp`** (`app/api/notes.py`) - Note creation, listing, preview, and printing
- **`templates_bp`** (`app/api/templates.py`) - Template CRUD operations
- **`health_bp`** (`app/api/health.py`) - Health checks for DB and printer

### Database Schema

**`notes` table:**
- `id` (serial PK), `category`, `text`, `date` (ticket/paper ID derives from `id`)
- `image_path`, `html_content` - Rendered outputs
- `template_id` (FK to note_templates), `printed` (boolean), `created_at`

**`note_templates` table:**
- `id` (serial PK), `name` (unique), `template_html`
- `is_active` (boolean), `created_at`

### Request/Response Validation

Marshmallow schemas (`app/schemas/`) handle validation and serialization:
- `NoteCreateSchema`, `NoteResponseSchema`, `NoteQuerySchema`
- `NoteTemplateCreateSchema`, `NoteTemplateResponseSchema`, `NoteTemplateUpdateSchema`
- `PaginationSchema` - Standardized pagination metadata

## Development Setup

### Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api flask db upgrade

# Seed default template
docker-compose exec api flask seed-default-template

# View logs
docker-compose logs -f api

# Run tests in container
docker-compose exec api pytest
```

### Local Development

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies including dev tools
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Set environment variables (copy from .env.example)
export DATABASE_URL="postgresql://user:pass@localhost/adhd_printer"
export SECRET_KEY="your-secret-key"
export PRINTER_ENABLED=false  # Use mock printer for development

# Run migrations
flask db upgrade

# Seed default template
flask seed-default-template

# Run development server
flask run --debug

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

## Common Commands

### API Usage (via curl)

```bash
# Create a note
curl -X POST http://localhost:5000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{"category": "trabalho", "text": "Complete documentation"}'

# List notes (paginated)
curl "http://localhost:5000/api/notes/?page=1&per_page=20"

# Get specific note
curl http://localhost:5000/api/notes/1

# Preview note as HTML
curl "http://localhost:5000/api/notes/1/preview?format=html"

# Preview note as image (download PNG)
curl "http://localhost:5000/api/notes/1/preview?format=image" --output note.png

# Print existing note
curl -X POST http://localhost:5000/api/notes/1/print

# Create template
curl -X POST http://localhost:5000/api/templates/ \
  -H "Content-Type: application/json" \
  -d '{"name": "custom", "template_html": "<html>...</html>"}'

# Health check
curl http://localhost:5000/health/
```

### Database Migrations

```bash
# Create new migration after model changes
flask db migrate -m "Add new field to notes"

# Apply migrations
flask db upgrade

# Rollback one migration
flask db downgrade

# Show migration history
flask db history
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_printer_service.py

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run integration tests only
pytest tests/integration/

# Run tests matching pattern
pytest -k "test_create_note"

# Run with real printer (hardware required)
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

## Key Implementation Details

### Image Rendering Pipeline

**Flow: HTML Template → Playwright → PNG → Thermal Printer**

1. **Template Processing** (`NoteRendererService.build_html`)
   - Replace placeholders: `{{ ticket_id }}`, `{{ category_icon }}`, `{{ text }}`, `{{ date }}`, `{{ width }}`
   - HTML-escape user input, convert newlines to `<br />`
   - Resolve category to emoji icon

2. **Playwright Rendering** (`NoteRendererService.render_to_png`)
   - Launch headless Chromium with `--no-sandbox` (Docker-compatible)
   - Set viewport with 2x device scale factor for crisp output
   - Load HTML, wait for `networkidle` event
   - Measure `.note` element bounding box
   - Screenshot with 6px clip padding
   - Output as PNG

3. **Printer Preparation** (`PrinterService._prepare_image`)
   - Convert to grayscale (Pillow `"L"` mode)
   - Resize if width > 384px (MAX_THERMAL_WIDTH_PX)
   - Pad width to multiple of 8 (ESC/POS byte alignment)
   - Convert to 1-bit monochrome (`"1"` mode)

4. **Thermal Printing** (`PrinterService.print_image`)
   - Send via `escpos.printer.Usb`
   - Use `bitImageRaster` implementation
   - Advance paper 15mm for tear-off margin

### Printer Service Abstraction

The printer service uses an abstract base class for testability:

- **`PrinterService`** - Real USB printer communication
- **`MockPrinterService`** - Test double that records print calls
- **`get_printer_service()`** - Factory function controlled by `PRINTER_ENABLED` env var

This allows tests to run without hardware and enables printer communication testing via the `MockPrinterService` inspection methods.

### Configuration Management

All configuration via environment variables (`app/config.py`):
- Pydantic Settings for type-safe config validation
- `.env` file support (not committed to git)
- Separate settings for dev/test/production via `FLASK_ENV`

Critical settings:
- `DATABASE_URL` - PostgreSQL connection string
- `PRINTER_*` - USB vendor/product IDs, endpoints
- `SECRET_KEY` - Flask session signing (must be random in production)
- `UPLOAD_FOLDER` - Where rendered PNGs are stored

### USB Printer Configuration

**Finding USB IDs:**
```bash
# Linux
lsusb
# Example output: Bus 001 Device 002: ID 6868:0200

# Extract values for .env:
# PRINTER_VENDOR_ID=0x6868
# PRINTER_PRODUCT_ID=0x0200
```

**Docker USB Passthrough:**

Edit `docker-compose.yml` to add device mapping:
```yaml
api:
  devices:
    - /dev/bus/usb/001/002:/dev/bus/usb/001/002
  privileged: true
  environment:
    - PRINTER_ENABLED=true
```

**Proxmox LXC:**
1. Find USB device on host: `lsusb`
2. Add to container config: Container → Hardware → USB Device
3. Set `PRINTER_ENABLED=true` in docker-compose environment

## Testing Strategy

### Unit Tests (`tests/unit/`)

- **`test_printer_service.py`** - Mock and real printer tests
  - `test_print_with_real_printer` - Skipped by default, requires hardware
  - Run with: `pytest -m real_printer` (after configuring markers)

- **`test_template_service.py`** - Template CRUD operations
- **`test_note_renderer.py`** - HTML rendering and image generation

### Integration Tests (`tests/integration/`)

- **`test_notes_api.py`** - Full request/response cycle for notes endpoints
- **`test_templates_api.py`** - Template API integration
- **`test_health_api.py`** - Health check endpoint

### Test Fixtures (`tests/conftest.py`)

- `app` - Flask application with SQLite in-memory DB
- `client` - Flask test client for API requests
- `sample_template` - Pre-created template for tests
- `sample_note` - Pre-created note for tests
- `mock_printer` - Access to MockPrinterService instance

## API Documentation

- **Swagger UI:** http://localhost:5000/swagger
- **OpenAPI spec:** http://localhost:5000/swagger.json

The API self-documents via Flask-Smorest decorators on endpoint methods.

## 12-Factor App Compliance

1. **Codebase** - Single Git repository
2. **Dependencies** - Explicit in `pyproject.toml`
3. **Config** - Environment variables in `.env`
4. **Backing Services** - PostgreSQL and printer as attached resources
5. **Build/Release/Run** - Dockerfile multi-stage build
6. **Processes** - Stateless Flask app (no local session storage)
7. **Port Binding** - Self-contained with Gunicorn WSGI server
8. **Concurrency** - Scale horizontally via multiple containers
9. **Disposability** - Fast startup (~5s), graceful shutdown
10. **Dev/Prod Parity** - Docker Compose for all environments
11. **Logs** - JSON structured logs to stdout
12. **Admin Processes** - Flask CLI commands (`flask db`, `flask seed-default-template`)

## Dependencies

**Core:**
- `flask` - Web framework
- `flask-sqlalchemy` - ORM
- `flask-migrate` - Database migrations (Alembic)
- `flask-smorest` - REST API + OpenAPI docs
- `marshmallow` - Request/response validation
- `psycopg2-binary` - PostgreSQL driver
- `gunicorn` - Production WSGI server

**Rendering/Printing:**
- `playwright` - Browser automation
- `pillow` - Image processing
- `python-escpos` - Thermal printer protocol
- `pyusb` - USB communication

**Configuration:**
- `python-dotenv` - `.env` file loading
- `pydantic-settings` - Type-safe config

**Testing:**
- `pytest`, `pytest-flask`, `pytest-cov`, `pytest-mock`
- `factory-boy` - Test data factories
- `faker` - Fake data generation

## File Structure

```
app/
├── __init__.py          # Application factory (create_app)
├── config.py            # Pydantic Settings
├── models/              # SQLAlchemy models
│   ├── base.py          # db object
│   ├── note.py          # Note model
│   └── note_template.py # NoteTemplate model
├── schemas/             # Marshmallow schemas
│   ├── note.py          # Note validation
│   ├── note_template.py # Template validation
│   └── pagination.py    # Pagination metadata
├── services/            # Business logic
│   ├── printer.py       # Printer abstraction
│   ├── note_renderer.py # HTML → PNG
│   ├── note_service.py  # Note operations
│   └── template_service.py # Template operations
├── api/                 # REST endpoints
│   ├── notes.py         # Notes blueprint
│   ├── templates.py     # Templates blueprint
│   └── health.py        # Health check
└── utils/
    └── cli.py           # Flask CLI commands

tests/
├── conftest.py          # Pytest fixtures
├── unit/                # Unit tests
└── integration/         # API integration tests
```

## Common Pitfalls

1. **Migrations not applied** - Always run `flask db upgrade` after pulling changes
2. **No default template** - Run `flask seed-default-template` before creating notes
3. **Printer not found** - Check USB passthrough config and `PRINTER_ENABLED=true`
4. **Port already in use** - Stop existing containers: `docker-compose down`
5. **Permission denied on uploads** - Ensure `UPLOAD_FOLDER` is writable by container user (UID 1000)
