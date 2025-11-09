# FastText Models

This directory contains FastText pre-trained word embedding models.

## Current Model

**wiki-news-300d-1M.vec**
- Source: https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip
- Language: English
- Dimensions: 300
- Vocabulary: 1 million words
- Training data: Wikipedia 2017, UMBC webbase corpus, and statmt.org news dataset (16B tokens)
- Format: Text format (.vec) - first line contains vocab size and dimensions, subsequent lines contain word and vector

## Usage

To load this model in Python:

```python
import fasttext.util

# Note: FastText typically uses .bin format, but we can load .vec format too
# For .vec format, use gensim or load manually
from gensim.models import KeyedVectors

model = KeyedVectors.load_word2vec_format('data/fasttext/wiki-news-300d-1M.vec')
vector = model['king']
```

Or for use with the fasttext library, convert to .bin format first.

## Alternative: Using fasttext library directly

If you need the .bin format for full FastText functionality:

```bash
# Download the .bin version instead
curl -O https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M-subword.bin.zip
unzip wiki-news-300d-1M-subword.bin.zip
```

The subword version (.bin) allows for out-of-vocabulary word embeddings using character n-grams.

## Model Info

- License: Creative Commons Attribution-Share-Alike License 3.0
- Citation: P. Bojanowski, E. Grave, A. Joulin, T. Mikolov, Enriching Word Vectors with Subword Information
