# justfile for FindWord project
# Run `just --list` to see all available commands

# Default recipe to display help
default:
    @just --list

# === Environment Management ===

# Sync dependencies using uv
Sync-Environment:
    uv sync

# Initial project setup: sync environment and run migrations
Setup-Project: Sync-Environment Run-Migrations
    @echo "✓ Project setup complete!"

# === Data Creation ===

# Download FastText pre-trained model
Download-Model:
    @echo "Downloading FastText model..."
    bash scripts/download_fasttext_model.sh

# Test FastText model to verify it works
Test-Fasttext:
    @echo "Testing FastText model..."
    uv run play/01_test_fasttext.py

# Execute play scripts and convert to notebooks
Create-Notebooks:
    @echo "Creating notebooks from play scripts..."
    uv run scripts/execute_and_convert.py

# Load words from CSV into Django database
Load-Words:
    @echo "Loading words into database..."
    uv run python manage.py loadwords --clear

# Create all data files from scratch (for fresh clone)
Create-Data: Download-Model Test-Fasttext Load-Words
    @echo "✓ All data created successfully!"

# === Development ===

# Start Django development server
Start-Server:
    uv run python manage.py runserver

# Run Django migrations
Run-Migrations:
    uv run python manage.py migrate

# Run Django tests
Run-Tests:
    uv run python manage.py test

# Start Django shell
Start-Shell:
    uv run python manage.py shell

# Create Django superuser
Create-Superuser:
    uv run python manage.py createsuperuser

# === Docker ===

# Build Docker images
Build-Image:
    docker-compose build

# Start Docker containers
Start-Docker:
    docker-compose up -d

# Stop Docker containers
Stop-Docker:
    docker-compose down

# View Docker logs
Show-Logs:
    docker-compose logs -f

# === Utilities ===

# Remove generated data files (keeps FastText model)
Clean-Data:
    @echo "Cleaning generated data files..."
    rm -f data/db.sqlite3
    rm -f data/words.csv
    rm -f play/*.ipynb
    @echo "✓ Data cleaned!"

# Remove all data including FastText model
Clean-All: Clean-Data
    @echo "Cleaning FastText model..."
    rm -f data/fasttext/*.vec
    @echo "✓ All data cleaned!"

# Show project status
Show-Status:
    @echo "=== Project Status ==="
    @echo ""
    @echo "FastText model:"
    @ls -lh data/fasttext/*.vec 2>/dev/null || echo "  Not downloaded"
    @echo ""
    @echo "Database:"
    @ls -lh data/db.sqlite3 2>/dev/null || echo "  Not created"
    @echo ""
    @echo "Words CSV:"
    @ls -lh data/words.csv 2>/dev/null || echo "  Not created"
    @echo ""
    @echo "Virtual environment:"
    @if [ -d .venv ]; then echo "  Synced"; else echo "  Not synced"; fi
