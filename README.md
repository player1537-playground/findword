# claude-playground

A Django-based API project for word finding and FastText integration.

## Project Structure

```
claude-playground/
├── src/
│   ├── core/                    # Django project settings
│   │   ├── __init__.py
│   │   ├── settings.py          # Main settings file
│   │   ├── urls.py              # Root URL configuration
│   │   ├── asgi.py              # ASGI configuration
│   │   └── wsgi.py              # WSGI configuration
│   └── findword_api/            # Main Django app
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── tests.py
│       ├── migrations/
│       │   └── __init__.py
│       └── management/
│           └── commands/        # Custom management commands
│               └── __init__.py
├── data/                        # Runtime data files
│   ├── fasttext/                # FastText models storage
│   └── db.sqlite3               # SQLite database (created after migration)
├── temp/                        # Temporary files
├── play/                        # Exploration and test scripts
├── manage.py                    # Django management script
└── requirements.txt             # Python dependencies

```

## Setup Instructions

### 1. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## Dependencies

- Django >= 4.2
- fasttext - For word embeddings
- numpy - Numerical computations
- scikit-learn - Machine learning utilities
- matplotlib - Visualization
- jupytext - Jupyter notebook conversion
- pandas - Data manipulation
- tqdm - Progress bars

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Custom Management Commands

Add new management commands in `src/findword_api/management/commands/`

### API Endpoints

API endpoints are configured under `/api/` path. See `src/core/urls.py` and `src/findword_api/urls.py` for routing.

## Configuration

Key settings in `src/core/settings.py`:

- `BASE_DIR`: Points to the project root
- `DATABASES`: SQLite database stored in `data/db.sqlite3`
- `FASTTEXT_MODELS_DIR`: FastText models directory at `data/fasttext/`
- `TEMP_DIR`: Temporary files directory
- `STATIC_ROOT`: Static files collected to `staticfiles/`
- `MEDIA_ROOT`: User-uploaded files stored in `data/media/`