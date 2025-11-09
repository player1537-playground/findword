# Project Plan: Semantic Word Similarity Finder

## Project Overview
Build a Django-based application that finds nouns and verbs with similar semantic meanings using FastText embeddings. The system will maintain a database of words with their part-of-speech tags and vector embeddings, enabling semantic similarity searches.

## Technology Stack
- **Backend**: Django
- **Embeddings**: FastText (https://github.com/facebookresearch/fastText)
- **Development**: uv for dependency management, jupytext for notebook conversion
- **Visualization**: t-SNE with PCA preprocessing
- **Data Source**: Word lists from https://gist.github.com/player1537/2caccbdd58b42d75cac473be6e9a1a71

## Directory Structure
```
.
├── data/                    # Runtime data files
│   ├── words.csv           # Final word database (word, noun, verb, embd)
│   └── fasttext/           # FastText model files
├── temp/                    # Temporary processing files
├── play/                    # Exploration scripts (uv run shebang style)
│   ├── 01_test_fasttext.py
│   ├── 02_embed_words.py
│   └── 03_tsne_viz.py
├── src/
│   ├── core/
│   │   ├── settings.py     # Django settings
│   │   └── ...
│   └── findword_api/        # Main Django app
│       ├── models.py
│       ├── views.py
│       └── management/
│           └── commands/
│               └── loadwords.py
└── requirements.txt / pyproject.toml
```

## Milestone 1: Environment Setup & FastText Exploration
**Goal**: Set up project structure and verify FastText embeddings work correctly.

**Tasks**:
1. **Use subagent** to initialize Django project structure
   - Create Django project with `src/core/settings.py`
   - Create `src/findword_api` app
   - Configure basic settings (database, apps, etc.)

2. **Use subagent** to create play directory exploration scripts
   - `play/01_test_fasttext.py`: Load FastText model and test basic embeddings
     - Use uv run shebang with inline script dependencies
     - Dependencies: `fasttext`, `numpy`
     - Test embedding 1-2 sample words
     - Print embedding dimensions and sample values

   - `play/02_embed_words.py`: Process a small word list through embeddings
     - Take command-line args for input words.txt and output embeddings file
     - Load FastText model
     - Generate embeddings for each word
     - Save results to temp/

   - `play/03_tsne_viz.py`: Visualize embedding space
     - Take args: words.txt file, line limit, output image path
     - Load embeddings for words
     - Apply PCA to reduce to 8 dimensions first
     - Apply t-SNE for 2D visualization
     - Dependencies: `fasttext`, `numpy`, `scikit-learn`, `matplotlib`
     - Generate scatter plot with word labels

   - Configure jupytext to convert all play/*.py scripts to notebooks
     - Add jupytext config for .py -> .ipynb conversion
     - Use percent format for cell boundaries

3. **Use subagent** to download and set up FastText model
   - Download pre-trained FastText model (e.g., wiki-news-300d-1M)
   - Store in `data/fasttext/`
   - Document model source and version in README

4. **Manual verification** of play scripts
   - Run each play script to verify functionality
   - Review generated Jupyter notebooks
   - Ensure visualizations are clear and informative

**Deliverables**:
- Working Django project structure
- 3 exploration scripts with jupytext integration
- FastText model downloaded and accessible
- Generated notebook examples

---

## Milestone 2: Word List Processing & Part-of-Speech Detection
**Goal**: Build the words.csv database with noun/verb classifications and embeddings.

**Tasks**:
1. **Use subagent** to fetch and parse word lists from gist
   - Download files from https://gist.github.com/player1537/2caccbdd58b42d75cac473be6e9a1a71
   - Parse filename format: `pos=<part>,lang=en,length=<n>.txt`
   - Extract words and their part-of-speech tags
   - Store raw data in `temp/raw_words/`

2. **Use subagent** to create word classification script
   - Script: `temp/classify_words.py`
   - Read all word files from gist
   - Determine if each word can be noun (Y/N) and/or verb (Y/N)
   - Handle multi-POS words (e.g., "run" is both noun and verb)
   - Output: `temp/words_classified.csv` with columns: word, noun, verb

3. **Use subagent** to create embedding generation script
   - Script: `temp/generate_embeddings.py`
   - Read `temp/words_classified.csv`
   - For each word, generate FastText embedding
   - Add embedding as JSON array column
   - Output: `data/words.csv` with columns: word, noun, verb, embd
   - Optimize for batch processing (process in chunks if needed)

4. **Manual validation** of data quality
   - Verify sample entries in words.csv
   - Check embedding dimensions are consistent
   - Verify noun/verb classifications are accurate

**Deliverables**:
- `data/words.csv` with complete word database
- Word list extraction scripts in temp/
- Classification and embedding generation scripts
- Data quality validation report

---

## Milestone 3: Django Models & Data Loading
**Goal**: Create Django models and load word data into the database.

**Tasks**:
1. **Use subagent** to design Django models
   - File: `src/findword_api/models.py`
   - Model: `Word`
     - Fields:
       - `word` (CharField, unique=True, indexed)
       - `is_noun` (BooleanField)
       - `is_verb` (BooleanField)
       - `embedding` (JSONField) - store embedding vector
       - `created_at`, `updated_at` (DateTimeField)
     - Methods:
       - `get_similar_words(limit=10)` - find semantically similar words
       - `cosine_similarity(other_word)` - calculate similarity score
   - Run migrations

2. **Use subagent** to create management command
   - File: `src/findword_api/management/commands/loadwords.py`
   - Command: `python manage.py loadwords`
   - Features:
     - Read `data/words.csv`
     - Use `Word.objects.update_or_create(word=..., defaults={...})`
     - Batch processing for performance (bulk_create with chunking)
     - Progress bar showing load status
     - Option to clear database first (`--clear` flag)
     - Dry-run mode (`--dry-run` flag)
   - Error handling:
     - Skip malformed entries
     - Log errors to temp/loadwords_errors.log
     - Summary report at end

3. **Use subagent** to create database indexes
   - Add database indexes for common queries
   - Index on `word` field (already unique)
   - Consider GiST index for similarity searches if using PostgreSQL

4. **Manual testing** of data loading
   - Run `python manage.py loadwords`
   - Verify record counts match CSV
   - Test sample queries for word lookups
   - Verify embedding data is correctly stored and retrievable

**Deliverables**:
- Django Word model with methods
- loadwords management command
- Database populated with word data
- Migration files

---

## Milestone 4: API Endpoints & Similarity Search
**Goal**: Build REST API endpoints for word similarity searches.

**Tasks**:
1. **Use subagent** to implement similarity search algorithm
   - File: `src/findword_api/similarity.py`
   - Function: `find_similar_words(target_word, part_of_speech=None, limit=10)`
     - Load target word embedding
     - Filter by part-of-speech if specified (noun/verb)
     - Calculate cosine similarity with all candidate words
     - Return top N most similar words
   - Optimize:
     - Consider caching strategies
     - Use numpy for vectorized operations
     - Precompute normalized embeddings if needed

2. **Use subagent** to create Django REST API views
   - Install Django REST Framework
   - File: `src/findword_api/views.py`
   - Endpoints:
     - `GET /api/words/{word}/` - Get word details
     - `GET /api/words/{word}/similar/` - Find similar words
       - Query params: `pos` (noun/verb), `limit` (default 10)
     - `GET /api/search/?q=<word>` - Search for words
   - Serializers in `src/findword_api/serializers.py`

3. **Use subagent** to add API documentation
   - Set up Swagger/OpenAPI documentation
   - Document all endpoints with examples
   - Include response schemas

4. **Manual API testing**
   - Test similarity searches with various words
   - Verify noun/verb filtering works
   - Check performance with timing tests
   - Test edge cases (unknown words, empty results)

**Deliverables**:
- Working similarity search algorithm
- REST API endpoints
- API documentation
- Test results and performance metrics

---

## Milestone 5: Frontend & Visualization
**Goal**: Create a simple web interface for exploring word similarities.

**Tasks**:
1. **Use subagent** to create simple HTML/JS frontend
   - Template: `src/findword_api/templates/index.html`
   - Features:
     - Search box for input word
     - Radio buttons for noun/verb filter
     - Display similar words in a list
     - Show similarity scores
     - Click on result to search that word
   - Use HTMX or vanilla JS for dynamic updates

2. **Use subagent** to add visualization endpoint
   - Endpoint: `GET /api/words/{word}/visualize/`
   - Generate t-SNE plot showing:
     - Target word
     - Similar words
     - Color-coded by noun/verb
   - Return as image or interactive plot (matplotlib or plotly)

3. **Manual UI testing**
   - Test search functionality
   - Verify visualization renders correctly
   - Check responsiveness and usability

**Deliverables**:
- Web interface for word similarity search
- Visualization of semantic space
- User documentation

---

## Milestone 6: Testing, Documentation & Deployment
**Goal**: Finalize project with tests, documentation, and deployment preparation.

**Tasks**:
1. **Use subagent** to write tests
   - Unit tests for similarity functions
   - Integration tests for API endpoints
   - Test data loading command
   - Test edge cases and error handling

2. **Use subagent** to create comprehensive documentation
   - README.md with:
     - Project overview
     - Setup instructions
     - Usage examples
     - API documentation
   - Architecture documentation
   - Data pipeline documentation

3. **Use subagent** to add deployment configuration
   - Docker configuration
   - Environment variable setup
   - Production settings
   - Database configuration for PostgreSQL

4. **Manual deployment testing**
   - Test installation on fresh environment
   - Verify all dependencies install correctly
   - Run full pipeline end-to-end

**Deliverables**:
- Test suite with good coverage
- Complete documentation
- Deployment-ready configuration
- Deployment guide

---

## Key Design Decisions

### Data Pipeline
1. Word lists → Classification (noun/verb) → Embedding generation → CSV
2. CSV → Django management command → Database
3. Database → API → Frontend

### FastText Model
- Use pre-trained model (e.g., wiki-news-300d-1M) for English
- Store in `data/fasttext/` directory
- Consider model size vs. accuracy tradeoffs

### Database Choice
- SQLite for development (default Django)
- PostgreSQL recommended for production (better JSON support)
- Consider vector extension (pgvector) for future optimization

### Performance Considerations
- Batch processing for data loading
- Consider caching for frequent similarity searches
- Use numpy for vectorized similarity calculations
- Precompute normalized embeddings

### Subagent Usage Strategy
- Use subagents for each major component implementation
- Use subagents for complex setup tasks (Django structure, data processing)
- Keep manual tasks for validation and testing phases
- Use subagents for documentation generation

---

## Dependencies
- Django >= 4.2
- fasttext
- numpy
- scikit-learn
- matplotlib
- jupytext
- djangorestframework (for API)
- pandas (for CSV processing)
- tqdm (for progress bars)

---

## Future Enhancements
- Add support for adjectives and adverbs
- Implement phrase/sentence embeddings
- Add user accounts and saved searches
- Implement vector database (Pinecone, Weaviate) for scaling
- Add multilingual support
- Fine-tune embeddings on domain-specific corpus
