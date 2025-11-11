# FindWord - Semantic Word Similarity Search API

A Django-based REST API that finds semantically similar words using FastText embeddings. Features include word similarity search, semantic space visualization with t-SNE, and an interactive web interface.

## Features

- **Semantic Word Similarity Search**: Find words with similar meanings using cosine similarity on FastText embeddings
- **Part-of-Speech Filtering**: Filter results by noun, verb, or any part of speech
- **Interactive Web Interface**: Modern, responsive UI for searching and exploring word similarities
- **t-SNE Visualization**: Visualize the semantic space of a word and its similar words
- **RESTful API**: Full REST API with comprehensive documentation
- **Production Ready**: Docker, Docker Compose, and comprehensive deployment guide included

## Project Structure

```
claude-playground/
├── src/
│   ├── core/                           # Django project settings
│   │   ├── settings.py                 # Main configuration
│   │   ├── urls.py                     # Root URL routing
│   │   ├── wsgi.py                     # WSGI configuration
│   │   └── asgi.py                     # ASGI configuration
│   └── findword_api/                   # Main Django application
│       ├── models.py                   # Word model with embedding support
│       ├── views.py                    # API views and web interface
│       ├── urls.py                     # API endpoint routing
│       ├── similarity.py                # Similarity search algorithm
│       ├── serializers.py               # DRF serializers
│       ├── templates/                  # HTML templates
│       │   └── findword_api/
│       │       ├── base.html           # Base template with styling
│       │       └── index.html          # Main search interface
│       ├── management/commands/        # Custom Django commands
│       │   └── loadwords.py            # Command to load words from CSV
│       └── tests.py                    # Comprehensive test suite
├── data/
│   ├── fasttext/                       # FastText models
│   └── db.sqlite3                      # SQLite database (created after migrate)
├── temp/                               # Temporary processing files
├── play/                               # Exploration scripts
├── Dockerfile                          # Docker image definition
├── docker-compose.yml                  # Docker Compose configuration
├── nginx.conf                          # Nginx reverse proxy config
├── PLAN.md                             # Project plan and milestones
├── DEPLOYMENT.md                       # Deployment guide
├── requirements.txt                    # Python dependencies
└── manage.py                           # Django management utility
```

## Technology Stack

- **Backend**: Django 4.2+, Django REST Framework
- **Embeddings**: FastText (pre-trained models)
- **Similarity**: Cosine similarity with numpy
- **Visualization**: t-SNE with PCA preprocessing, matplotlib
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Caching**: Redis (optional)
- **Deployment**: Docker, Docker Compose, Gunicorn, Nginx

## Git LFS (Large File Storage)

This repository uses Git LFS to manage some data files. The following files are tracked with Git LFS:

- `temp/raw_words/*.txt` - Raw word lists extracted by part-of-speech and length (~10 MB total)
- `temp/words_classified.csv` - Classified words with POS tags (~1.3 MB)

**Note**: Very large files (`data/words.csv` and FastText models) are NOT tracked in git. See instructions below to obtain them.

### Installing Git LFS

Before cloning the repository, install Git LFS:

**Ubuntu/Debian:**
```bash
apt-get install git-lfs
```

**macOS:**
```bash
brew install git-lfs
```

**Windows:**
Download from https://git-lfs.github.com/

After installation, initialize Git LFS:
```bash
git lfs install
```

### Cloning with Git LFS

When you clone the repository, Git LFS will automatically download the large files:

```bash
git clone <repository-url>
cd claude-playground
```

If you've already cloned the repository before Git LFS was set up, fetch the LFS files:

```bash
git lfs fetch --all
git lfs checkout
```

### Working with LFS Files

Git LFS is transparent in normal usage. When you commit changes to tracked files, they're automatically handled by LFS. The files appear and behave like normal files in your working directory.

To see which files are tracked by LFS:
```bash
git lfs ls-files
```

## Getting Large Files

Due to their size, the FastText model and generated embeddings are not stored in git.

### Download FastText Model

Download the pre-trained FastText model (2.2 GB):

```bash
cd data/fasttext
curl -L -O https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip
unzip wiki-news-300d-1M.vec.zip
rm wiki-news-300d-1M.vec.zip
```

### Generate Embeddings

After downloading the FastText model, generate the embeddings file (takes ~5 minutes):

```bash
# From the project root
./temp/generate_embeddings.py
```

This will create `data/words.csv` (225 MB) with FastText embeddings for 36,000+ words.

## Quick Start

### Local Development

1. **Clone the repository**:
```bash
git clone <repository-url>
cd claude-playground
```

2. **Create and activate virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Download FastText model and generate embeddings**:
```bash
# Download model (2.2 GB)
cd data/fasttext
curl -L -O https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip
unzip wiki-news-300d-1M.vec.zip
rm wiki-news-300d-1M.vec.zip
cd ../..

# Generate embeddings (takes ~5 minutes)
./temp/generate_embeddings.py
```

5. **Run migrations**:
```bash
python manage.py migrate
```

6. **Load word data**:
```bash
python manage.py loadwords --clear
```

7. **Start development server**:
```bash
python manage.py runserver
```

8. **Access the application**:
   - Web Interface: http://localhost:8000/
   - API Docs: http://localhost:8000/api/docs/
   - API Root: http://localhost:8000/api/

### Docker Deployment

1. **Build and run with Docker Compose**:
```bash
docker-compose up -d
```

This will start:
- Django application on port 8000
- PostgreSQL database
- Redis cache
- Nginx reverse proxy on port 80

2. **Create superuser** (optional):
```bash
docker-compose exec web python manage.py createsuperuser
```

3. **Access the application**:
   - Web Interface: http://localhost/
   - API: http://localhost/api/

## API Endpoints

### Web Interface
- `GET /` - Main web interface with search form

### Words
- `GET /api/words/` - List all words (paginated)
- `GET /api/words/{word}/` - Get word details
- `GET /api/words/{word}/similar/` - Find similar words
- `GET /api/words/{word}/visualize/` - Generate t-SNE visualization

### Search
- `GET /api/search/?q=<query>` - Search for words by prefix or exact match

### Documentation
- `GET /api/docs/` - Interactive API documentation (Swagger)
- `GET /api/schema/` - OpenAPI schema

## API Usage Examples

### Find Similar Words

```bash
# Find 10 words similar to "dog"
curl "http://localhost:8000/api/words/dog/similar/"

# Filter by part of speech (noun)
curl "http://localhost:8000/api/words/dog/similar/?pos=noun"

# Get 20 results
curl "http://localhost:8000/api/words/dog/similar/?limit=20"

# Set minimum similarity threshold
curl "http://localhost:8000/api/words/dog/similar/?min_similarity=0.8"
```

### Search Words

```bash
# Prefix search
curl "http://localhost:8000/api/search/?q=dog"

# Exact match
curl "http://localhost:8000/api/search/?q=dog&exact=true"

# Filter by part of speech
curl "http://localhost:8000/api/search/?q=dog&pos=noun"
```

### Get Visualization

```bash
# Generate t-SNE visualization
curl "http://localhost:8000/api/words/dog/visualize/" > visualization.png

# Include more similar words
curl "http://localhost:8000/api/words/dog/visualize/?limit=20" > visualization.png
```

## Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test class
python manage.py test findword_api.tests.WordModelTestCase

# Run with verbose output
python manage.py test --verbosity=2

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Project Milestones

### ✅ Milestone 1: Environment Setup & FastText Exploration
- Django project structure
- FastText exploration scripts
- Model download and setup

### ✅ Milestone 2: Word List Processing & Part-of-Speech Detection
- Word list extraction from gist
- POS classification
- Embedding generation

### ✅ Milestone 3: Django Models & Data Loading
- Word model with embeddings
- Management command for data loading
- Database indexing

### ✅ Milestone 4: API Endpoints & Similarity Search
- REST API endpoints
- Similarity search algorithm
- OpenAPI documentation

### ✅ Milestone 5: Frontend & Visualization
- Interactive web interface
- t-SNE visualization
- Modern responsive design

### ✅ Milestone 6: Testing, Documentation & Deployment
- Comprehensive test suite (50+ tests)
- Deployment guide
- Docker configuration

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive production deployment instructions including:
- PostgreSQL setup
- Gunicorn configuration
- Nginx reverse proxy
- SSL/TLS setup
- Systemd service configuration
- Monitoring and troubleshooting
- Scaling considerations

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/findword
REDIS_URL=redis://localhost:6379/0
```

### Django Settings

Key settings in `src/core/settings.py`:
- `DEBUG`: Enable/disable debug mode
- `DATABASES`: Database configuration
- `INSTALLED_APPS`: Installed Django apps
- `REST_FRAMEWORK`: DRF configuration
- `SPECTACULAR_SETTINGS`: OpenAPI documentation settings

## Performance Optimization

1. **Caching**: Enable Redis caching for similar word searches
2. **Database Indexes**: Word model has indexes on searchable fields
3. **Pagination**: API results are paginated (20 items per page)
4. **Vectorized Operations**: NumPy for fast similarity calculations
5. **PCA Preprocessing**: Reduces dimensions before t-SNE visualization

## Dependencies

### Core Dependencies
- `Django >= 4.2` - Web framework
- `djangorestframework` - REST API
- `drf-spectacular` - API documentation
- `fasttext` - Word embeddings
- `numpy` - Numerical computations
- `scikit-learn` - Machine learning utilities
- `matplotlib` - Visualization
- `pandas` - Data manipulation
- `tqdm` - Progress bars

### Optional Dependencies
- `psycopg2-binary` - PostgreSQL support
- `gunicorn` - Production WSGI server
- `django-redis` - Redis caching
- `coverage` - Test coverage

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes

### Testing
- Aim for 80%+ test coverage
- Test models, views, and utility functions
- Include edge cases and error handling

### Adding Features
1. Create feature branch
2. Write tests first
3. Implement feature
4. Update documentation
5. Run full test suite
6. Create pull request

## Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'django'**
- Install dependencies: `pip install -r requirements.txt`
- Activate virtual environment

**Database error on startup**
- Run migrations: `python manage.py migrate`
- Check database configuration in settings.py

**Static files not loading**
- Run: `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL settings

**Visualization endpoint returns error**
- Ensure scikit-learn is installed: `pip install scikit-learn`
- Check word has valid embedding

See [DEPLOYMENT.md](DEPLOYMENT.md) for more troubleshooting guides.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- [ ] Support for adjectives and adverbs
- [ ] Phrase/sentence embeddings
- [ ] User accounts and saved searches
- [ ] Vector database integration (Pinecone, Weaviate)
- [ ] Multilingual support
- [ ] Fine-tuned embeddings on domain-specific corpus
- [ ] Batch API for multiple queries
- [ ] Export results to CSV/JSON
- [ ] Advanced filtering and faceted search

## Support

For issues and questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
2. Review test cases in `tests.py` for usage examples
3. Check API documentation at `/api/docs/`
4. Review commit history in git log

## Acknowledgments

- FastText by Facebook Research
- Django community
- Django REST Framework
- scikit-learn for machine learning tools
