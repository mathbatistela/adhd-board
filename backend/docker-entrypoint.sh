#!/bin/bash
set -e

echo "========================================="
echo "ADHD Printer API - Starting up"
echo "========================================="

# Function to wait for PostgreSQL
wait_for_db() {
    echo "Waiting for PostgreSQL to be ready..."

    # Extract host and port from DATABASE_URL
    # Format: postgresql://user:pass@host:port/dbname
    if [ -z "$DATABASE_URL" ]; then
        echo "ERROR: DATABASE_URL is not set"
        exit 1
    fi

    # Parse DATABASE_URL to get host and port
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    # Default to localhost:5432 if parsing fails
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}

    echo "Checking connection to $DB_HOST:$DB_PORT..."

    # Wait up to 30 seconds for the database
    RETRIES=30
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U postgres 2>/dev/null || [ $RETRIES -eq 0 ]; do
        echo "Waiting for database... ($RETRIES attempts left)"
        RETRIES=$((RETRIES - 1))
        sleep 1
    done

    if [ $RETRIES -eq 0 ]; then
        echo "WARNING: Could not confirm database connection, proceeding anyway..."
    else
        echo "PostgreSQL is ready!"
    fi
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    if flask db upgrade; then
        echo "Migrations completed successfully!"
    else
        echo "ERROR: Migration failed!"
        exit 1
    fi
}

# Function to seed default template
seed_template() {
    echo "Seeding default template..."
    if flask seed-default-template; then
        echo "Default template seeded successfully!"
    else
        echo "WARNING: Failed to seed default template (may already exist)"
    fi
}

# Main startup sequence
echo "Environment: ${FLASK_ENV:-production}"
echo "Database: ${DATABASE_URL}"
echo "Printer enabled: ${PRINTER_ENABLED:-false}"
echo ""

# Wait for database
wait_for_db

# Run migrations
run_migrations

# Seed default template
seed_template

echo ""
echo "========================================="
echo "Starting application..."
echo "========================================="
echo ""

# Execute the main command (gunicorn or whatever is passed)
exec "$@"
