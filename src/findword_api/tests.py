"""
Comprehensive test suite for the FindWord application.

Tests cover:
- Model functionality (Word model, embeddings, similarity calculations)
- API endpoints (retrieval, search, similarity)
- Similarity search functionality
- Edge cases and error handling
"""

import json
import numpy as np
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Word
from .similarity import find_similar_words


class WordModelTestCase(TestCase):
    """Test cases for the Word model."""

    def setUp(self):
        """Set up test data."""
        # Create test embeddings
        self.embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.embedding2 = [0.15, 0.25, 0.35, 0.45, 0.55]
        self.embedding3 = [0.9, 0.8, 0.7, 0.6, 0.5]

        # Create test words
        self.word1 = Word.objects.create(
            word='dog',
            is_noun=True,
            is_verb=False,
            embedding=self.embedding1
        )
        self.word2 = Word.objects.create(
            word='cat',
            is_noun=True,
            is_verb=False,
            embedding=self.embedding2
        )
        self.word3 = Word.objects.create(
            word='run',
            is_noun=False,
            is_verb=True,
            embedding=self.embedding3
        )

    def test_word_creation(self):
        """Test word creation and basic attributes."""
        self.assertEqual(self.word1.word, 'dog')
        self.assertTrue(self.word1.is_noun)
        self.assertFalse(self.word1.is_verb)
        self.assertEqual(self.word1.embedding, self.embedding1)

    def test_word_string_representation(self):
        """Test string representation of word."""
        self.assertEqual(str(self.word1), 'dog')

    def test_get_embedding_array(self):
        """Test converting embedding to numpy array."""
        arr = self.word1.get_embedding_array()
        self.assertIsInstance(arr, np.ndarray)
        self.assertEqual(arr.dtype, np.float32)
        np.testing.assert_array_almost_equal(arr, self.embedding1)

    def test_get_embedding_array_invalid(self):
        """Test error handling for invalid embeddings."""
        word = Word.objects.create(
            word='invalid',
            is_noun=True,
            embedding=[]
        )
        with self.assertRaises(ValueError):
            word.get_embedding_array()

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        similarity = self.word1.cosine_similarity(self.word2)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, -1.0)
        self.assertLessEqual(similarity, 1.0)

        # Similar vectors should have high similarity
        self.assertGreater(similarity, 0.9)

    def test_cosine_similarity_different_dimensions(self):
        """Test error when vectors have different dimensions."""
        word_diff = Word.objects.create(
            word='different',
            is_noun=True,
            embedding=[0.1, 0.2]  # Different length
        )
        with self.assertRaises(ValueError):
            self.word1.cosine_similarity(word_diff)

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vectors."""
        word_zero = Word.objects.create(
            word='zero',
            is_noun=True,
            embedding=[0.0, 0.0, 0.0, 0.0, 0.0]
        )
        similarity = self.word1.cosine_similarity(word_zero)
        self.assertEqual(similarity, 0.0)

    def test_get_similar_words(self):
        """Test finding similar words."""
        similar = self.word1.get_similar_words(limit=2)
        self.assertIsInstance(similar, list)
        self.assertLessEqual(len(similar), 2)

        # Check that results are tuples of (Word, similarity)
        for word, sim in similar:
            self.assertIsInstance(word, Word)
            self.assertIsInstance(sim, float)
            self.assertNotEqual(word.id, self.word1.id)

    def test_get_similar_words_limit(self):
        """Test limit parameter in similarity search."""
        similar = self.word1.get_similar_words(limit=1)
        self.assertLessEqual(len(similar), 1)

    def test_get_similar_words_min_similarity(self):
        """Test minimum similarity threshold."""
        similar = self.word1.get_similar_words(min_similarity=0.95)
        for _, sim in similar:
            self.assertGreaterEqual(sim, 0.95)

    def test_get_similar_words_noun_filter(self):
        """Test filtering by noun part of speech."""
        similar = self.word1.get_similar_words(is_noun=True, limit=10)
        for word, _ in similar:
            self.assertTrue(word.is_noun)

    def test_get_similar_words_verb_filter(self):
        """Test filtering by verb part of speech."""
        similar = self.word1.get_similar_words(is_verb=True, limit=10)
        for word, _ in similar:
            self.assertTrue(word.is_verb)

    def test_get_similar_words_sorted_descending(self):
        """Test that results are sorted by similarity in descending order."""
        similar = self.word1.get_similar_words(limit=10)
        similarities = [sim for _, sim in similar]
        self.assertEqual(similarities, sorted(similarities, reverse=True))

    def test_model_ordering(self):
        """Test that words are ordered alphabetically by default."""
        words = Word.objects.all()
        word_list = [w.word for w in words]
        self.assertEqual(word_list, sorted(word_list))


class SimilarityFunctionTestCase(TestCase):
    """Test cases for the similarity search function."""

    def setUp(self):
        """Set up test data."""
        self.embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.embedding2 = [0.15, 0.25, 0.35, 0.45, 0.55]
        self.embedding3 = [0.9, 0.8, 0.7, 0.6, 0.5]

        self.word1 = Word.objects.create(
            word='dog', is_noun=True, is_verb=False, embedding=self.embedding1
        )
        self.word2 = Word.objects.create(
            word='cat', is_noun=True, is_verb=False, embedding=self.embedding2
        )
        self.word3 = Word.objects.create(
            word='run', is_noun=False, is_verb=True, embedding=self.embedding3
        )

    def test_find_similar_words_basic(self):
        """Test basic similar words search."""
        results = find_similar_words(target_word='dog', limit=2)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)

        for word, sim in results:
            self.assertIsInstance(word, Word)
            self.assertIsInstance(sim, float)

    def test_find_similar_words_not_found(self):
        """Test error when word not found."""
        with self.assertRaises(Word.DoesNotExist):
            find_similar_words(target_word='nonexistent')

    def test_find_similar_words_case_insensitive(self):
        """Test case-insensitive search."""
        results1 = find_similar_words(target_word='dog')
        results2 = find_similar_words(target_word='DOG')
        results3 = find_similar_words(target_word='DoG')

        self.assertEqual(len(results1), len(results2))
        self.assertEqual(len(results1), len(results3))

    def test_find_similar_words_pos_filter(self):
        """Test part of speech filtering."""
        results_noun = find_similar_words(target_word='dog', part_of_speech='noun')
        results_verb = find_similar_words(target_word='dog', part_of_speech='verb')

        for word, _ in results_noun:
            self.assertTrue(word.is_noun)

        for word, _ in results_verb:
            self.assertTrue(word.is_verb)

    def test_find_similar_words_limit(self):
        """Test limit parameter."""
        results = find_similar_words(target_word='dog', limit=1)
        self.assertLessEqual(len(results), 1)

    def test_find_similar_words_invalid_pos(self):
        """Test error with invalid POS parameter."""
        with self.assertRaises(ValueError):
            find_similar_words(target_word='dog', part_of_speech='invalid')


class WordAPITestCase(APITestCase):
    """Test cases for Word API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.embedding1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.embedding2 = [0.15, 0.25, 0.35, 0.45, 0.55]
        self.embedding3 = [0.9, 0.8, 0.7, 0.6, 0.5]

        self.word1 = Word.objects.create(
            word='dog', is_noun=True, is_verb=False, embedding=self.embedding1
        )
        self.word2 = Word.objects.create(
            word='cat', is_noun=True, is_verb=False, embedding=self.embedding2
        )
        self.word3 = Word.objects.create(
            word='run', is_noun=False, is_verb=True, embedding=self.embedding3
        )

        self.client = APIClient()

    def test_list_words(self):
        """Test listing all words."""
        response = self.client.get('/api/words/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 3)

    def test_retrieve_word(self):
        """Test retrieving a specific word."""
        response = self.client.get('/api/words/dog/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['word'], 'dog')
        self.assertTrue(response.data['is_noun'])
        self.assertFalse(response.data['is_verb'])

    def test_retrieve_word_case_insensitive(self):
        """Test case-insensitive word retrieval."""
        response = self.client.get('/api/words/DOG/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['word'].lower(), 'dog')

    def test_retrieve_word_not_found(self):
        """Test retrieving non-existent word."""
        response = self.client.get('/api/words/nonexistent/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_similar_words(self):
        """Test finding similar words endpoint."""
        response = self.client.get('/api/words/dog/similar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        for item in response.data:
            self.assertIn('word', item)
            self.assertIn('similarity', item)

    def test_similar_words_with_limit(self):
        """Test similar words with limit parameter."""
        response = self.client.get('/api/words/dog/similar/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 1)

    def test_similar_words_with_pos_filter(self):
        """Test similar words with part of speech filter."""
        response = self.client.get('/api/words/dog/similar/?pos=noun')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data:
            self.assertTrue(item['word']['is_noun'])

    def test_similar_words_invalid_pos(self):
        """Test error with invalid pos parameter."""
        response = self.client.get('/api/words/dog/similar/?pos=invalid')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_similar_words_invalid_limit(self):
        """Test handling of invalid limit parameter."""
        response = self.client.get('/api/words/dog/similar/?limit=not_a_number')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_similar_words_not_found(self):
        """Test similar words for non-existent word."""
        response = self.client.get('/api/words/nonexistent/similar/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SearchAPITestCase(APITestCase):
    """Test cases for the search endpoint."""

    def setUp(self):
        """Set up test data."""
        self.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        self.word1 = Word.objects.create(
            word='dog', is_noun=True, is_verb=False, embedding=self.embedding
        )
        self.word2 = Word.objects.create(
            word='dogs', is_noun=True, is_verb=False, embedding=self.embedding
        )
        self.word3 = Word.objects.create(
            word='dogma', is_noun=True, is_verb=False, embedding=self.embedding
        )
        self.word4 = Word.objects.create(
            word='cat', is_noun=True, is_verb=False, embedding=self.embedding
        )

        self.client = APIClient()

    def test_search_prefix_match(self):
        """Test prefix search (default)."""
        response = self.client.get('/api/search/?q=dog')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

        # Should find dog, dogs, dogma
        words = [item['word'] for item in response.data['results']]
        self.assertIn('dog', words)
        self.assertIn('dogs', words)
        self.assertIn('dogma', words)
        self.assertNotIn('cat', words)

    def test_search_exact_match(self):
        """Test exact match search."""
        response = self.client.get('/api/search/?q=dog&exact=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should find only 'dog'
        words = [item['word'] for item in response.data['results']]
        self.assertIn('dog', words)
        self.assertNotIn('dogs', words)
        self.assertNotIn('dogma', words)

    def test_search_no_query(self):
        """Test error when query is missing."""
        response = self.client.get('/api/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_with_pos_filter(self):
        """Test search with part of speech filter."""
        response = self.client.get('/api/search/?q=dog&pos=noun')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data['results']:
            self.assertTrue(item['is_noun'])

    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        response1 = self.client.get('/api/search/?q=dog')
        response2 = self.client.get('/api/search/?q=DOG')

        self.assertEqual(
            len(response1.data['results']),
            len(response2.data['results'])
        )


class IndexViewTestCase(TestCase):
    """Test cases for the index view."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_index_page_loads(self):
        """Test that index page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('FindWord', response.content.decode())

    def test_index_page_has_search_form(self):
        """Test that index page contains search form elements."""
        response = self.client.get('/')
        content = response.content.decode()
        self.assertIn('searchInput', content)
        self.assertIn('searchBtn', content)
        self.assertIn('visualizeBtn', content)


class APIRootTestCase(APITestCase):
    """Test cases for the API root endpoint."""

    def test_api_root(self):
        """Test API root endpoint."""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('endpoints', response.data)
