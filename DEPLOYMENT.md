# FindWord Deployment Guide

This document provides comprehensive instructions for deploying the FindWord application in various environments.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Management](#database-management)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

## Development Setup

### Prerequisites

- Python 3.8+
- pip or uv (recommended)
- SQLite3 (default database)
- Git

### Installation Steps

1. **Clone the repository:**

```bash
git clone <repository-url>
cd claude-playground
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

Using pip:
```bash
pip install -r requirements.txt
```

Using uv (faster):
```bash
uv pip install -r requirements.txt
```

4. **Run migrations:**

```bash
python manage.py migrate
```

5. **Create a superuser (optional):**

```bash
python manage.py createsuperuser
```

6. **Load word data:**

First, ensure you have the `data/words.csv` file. Then:

```bash
python manage.py loadwords --clear
```

7. **Run development server:**

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000/`

## Docker Deployment

### Building the Docker Image

1. **Build the image:**

```bash
docker build -t findword:latest .
```

2. **Run the container:**

```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DEBUG=False \
  -e SECRET_KEY='your-secret-key-here' \
  findword:latest
```

### Using Docker Compose

For a complete stack with PostgreSQL:

```bash
docker-compose up -d
```

This will:
- Start the Django application
- Start PostgreSQL database
- Run migrations automatically
- Load word data into the database

## Production Deployment

### Prerequisites for Production

- PostgreSQL 12+ (recommended over SQLite)
- Redis (for caching, optional but recommended)
- Nginx or Apache (reverse proxy)
- Gunicorn or uWSGI (WSGI server)
- Supervisor or systemd (process manager)

### Step-by-Step Production Setup

1. **Install production dependencies:**

```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary redis
```

2. **Configure environment variables:**

Create a `.env` file:

```
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/findword
REDIS_URL=redis://localhost:6379/0
DJANGO_SETTINGS_MODULE=core.settings
```

3. **Update settings.py for production:**

```python
# In src/core/settings.py
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# PostgreSQL Configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

# Redis Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Static files
STATIC_ROOT = '/var/www/findword/staticfiles'
MEDIA_ROOT = '/var/www/findword/media'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

4. **Run migrations:**

```bash
python manage.py migrate
```

5. **Collect static files:**

```bash
python manage.py collectstatic --noinput
```

6. **Create Gunicorn config** (`gunicorn_config.py`):

```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
```

7. **Start Gunicorn:**

```bash
gunicorn \
  --config gunicorn_config.py \
  --bind 0.0.0.0:8000 \
  core.wsgi:application
```

### Nginx Configuration

Create `/etc/nginx/sites-available/findword`:

```nginx
upstream findword {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/findword/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/findword/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://findword;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/findword /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Systemd Service

Create `/etc/systemd/system/findword.service`:

```ini
[Unit]
Description=FindWord Django Application
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/findword
Environment="PATH=/var/www/findword/venv/bin"
ExecStart=/var/www/findword/venv/bin/gunicorn \
    --config /var/www/findword/gunicorn_config.py \
    core.wsgi:application
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable findword
sudo systemctl start findword
```

## Environment Configuration

### Required Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DEBUG | False | Django debug mode |
| SECRET_KEY | (required) | Django secret key |
| ALLOWED_HOSTS | localhost | Comma-separated list of allowed hosts |
| DATABASE_URL | sqlite:///db.sqlite3 | Database connection URL |
| REDIS_URL | redis://localhost:6379/0 | Redis cache URL |

### Optional Settings

```python
# API Rate Limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## Database Management

### PostgreSQL Setup

1. **Create database and user:**

```bash
sudo -u postgres psql
CREATE DATABASE findword;
CREATE USER findword_user WITH PASSWORD 'secure_password';
ALTER ROLE findword_user SET client_encoding TO 'utf8';
ALTER ROLE findword_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE findword_user SET default_transaction_deferrable TO on;
ALTER ROLE findword_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE findword TO findword_user;
\q
```

2. **Set environment variables:**

```bash
export DATABASE_URL="postgresql://findword_user:secure_password@localhost:5432/findword"
```

3. **Run migrations:**

```bash
python manage.py migrate
```

### Backing Up the Database

**SQLite:**
```bash
cp data/db.sqlite3 data/db.sqlite3.backup
```

**PostgreSQL:**
```bash
pg_dump findword > findword_backup.sql
```

### Restoring the Database

**SQLite:**
```bash
cp data/db.sqlite3.backup data/db.sqlite3
```

**PostgreSQL:**
```bash
psql findword < findword_backup.sql
```

## Monitoring and Troubleshooting

### Health Checks

Create a health check endpoint or use curl:

```bash
curl http://localhost:8000/api/
```

### Logging

Configure logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/findword.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}
```

### Performance Optimization

1. **Enable caching:**

```python
@cache_page(60 * 5)  # Cache for 5 minutes
def some_view(request):
    pass
```

2. **Use select_related and prefetch_related:**

```python
words = Word.objects.select_related(...).prefetch_related(...)
```

3. **Database indexing:** Already configured in the Word model

4. **Enable GZIP compression:**

```python
MIDDLEWARE += ['django.middleware.gzip.GZipMiddleware']
```

### Common Issues and Solutions

**Issue: 500 error on word lookup**
- Check that embeddings are properly formatted
- Verify database has word data loaded

**Issue: Slow similarity searches**
- Increase cache timeout
- Consider using Redis
- Check database indexes are created

**Issue: Memory issues with large datasets**
- Batch process similarity searches
- Use pagination for list endpoints
- Consider vector database (Pinecone, Weaviate)

### Testing Production Setup

1. **Run tests:**

```bash
python manage.py test
```

2. **Load test data:**

```bash
python manage.py loadwords --dry-run
```

3. **Monitor logs:**

```bash
tail -f logs/findword.log
```

## Scaling Considerations

For production deployments with high traffic:

1. **Use load balancer** (HAProxy, AWS ELB)
2. **Multiple Gunicorn workers** across different servers
3. **PostgreSQL with replication** for high availability
4. **Redis cluster** for distributed caching
5. **CDN** for static files
6. **Vector database** (pgvector, Pinecone) for similarity search optimization
7. **Elasticsearch** for word search if needed

## Security Checklist

- [ ] Set DEBUG = False
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set SECURE_SSL_REDIRECT = True
- [ ] Enable CSRF protection
- [ ] Use environment variables for secrets
- [ ] Regular backups
- [ ] Keep dependencies updated
- [ ] Monitor logs for errors
- [ ] Set up rate limiting
- [ ] Use strong database passwords
