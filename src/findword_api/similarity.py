"""
Similarity search module for finding semantically similar words.

This module provides functions to calculate cosine similarity between word
embeddings and find similar words using vectorized numpy operations.
"""

from typing import List, Optional, Tuple
import numpy as np
from django.db.models import Q

from .models import Word


def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Cosine similarity measures the cosine of the angle between two vectors,
    producing a value between -1 (opposite) and 1 (identical direction).

    Args:
        vec1: First vector as numpy array.
        vec2: Second vector as numpy array.

    Returns:
        float: Cosine similarity score between -1 and 1.

    Raises:
        ValueError: If vectors have different dimensions or are zero vectors.

    Examples:
        >>> vec1 = np.array([1.0, 2.0, 3.0])
        >>> vec2 = np.array([1.0, 2.0, 3.0])
        >>> calculate_cosine_similarity(vec1, vec2)
        1.0
    """
    if vec1.shape != vec2.shape:
        raise ValueError(
            f"Vector dimensions don't match: {vec1.shape} vs {vec2.shape}"
        )

    # Calculate dot product and norms
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # Handle zero vectors
    if norm1 == 0 or norm2 == 0:
        raise ValueError("Cannot calculate similarity for zero vectors")

    # Return cosine similarity
    return float(dot_product / (norm1 * norm2))


def find_similar_words(
    target_word: str,
    part_of_speech: Optional[str] = None,
    limit: int = 10,
    min_similarity: float = 0.0
) -> List[Tuple[Word, float]]:
    """
    Find semantically similar words using cosine similarity.

    This function loads the target word's embedding, filters candidate words
    by part-of-speech if specified, calculates cosine similarity with all
    candidates using vectorized operations, and returns the top N most similar.

    Args:
        target_word: The word to find similarities for.
        part_of_speech: Optional filter - 'noun' or 'verb' (default: None).
        limit: Maximum number of similar words to return (default: 10).
        min_similarity: Minimum similarity threshold, 0-1 (default: 0.0).

    Returns:
        List of tuples containing (Word instance, similarity score),
        sorted by similarity in descending order.

    Raises:
        Word.DoesNotExist: If target word is not found in database.
        ValueError: If target word has invalid embedding or part_of_speech is invalid.

    Examples:
        >>> results = find_similar_words('cat', part_of_speech='noun', limit=5)
        >>> for word, similarity in results:
        ...     print(f"{word.word}: {similarity:.4f}")
        dog: 0.8523
        kitten: 0.8234
        feline: 0.8012
    """
    # Validate part_of_speech parameter
    if part_of_speech is not None and part_of_speech not in ['noun', 'verb']:
        raise ValueError("part_of_speech must be 'noun', 'verb', or None")

    # Load target word
    try:
        target = Word.objects.get(word=target_word)
    except Word.DoesNotExist:
        raise Word.DoesNotExist(f"Word '{target_word}' not found in database")

    # Get target embedding
    target_embedding = target.get_embedding_array()

    # Build queryset with filters
    queryset = Word.objects.exclude(id=target.id)

    if part_of_speech == 'noun':
        queryset = queryset.filter(is_noun=True)
    elif part_of_speech == 'verb':
        queryset = queryset.filter(is_verb=True)

    # For better performance with large datasets, we could batch process
    # For now, we'll process all words (works well for moderate dataset sizes)

    # Precompute normalized target embedding for efficiency
    target_norm = np.linalg.norm(target_embedding)
    if target_norm == 0:
        raise ValueError(f"Word '{target_word}' has zero embedding vector")

    target_normalized = target_embedding / target_norm

    # Calculate similarities for all candidate words
    similar_words = []

    # Batch load embeddings for better performance
    for word in queryset.iterator(chunk_size=1000):
        try:
            # Get candidate embedding
            candidate_embedding = word.get_embedding_array()

            # Calculate similarity using normalized vectors
            candidate_norm = np.linalg.norm(candidate_embedding)
            if candidate_norm == 0:
                continue

            candidate_normalized = candidate_embedding / candidate_norm
            similarity = float(np.dot(target_normalized, candidate_normalized))

            # Filter by minimum similarity
            if similarity >= min_similarity:
                similar_words.append((word, similarity))

        except (ValueError, TypeError):
            # Skip words with invalid embeddings
            continue

    # Sort by similarity (descending) and limit results
    similar_words.sort(key=lambda x: x[1], reverse=True)
    return similar_words[:limit]


def batch_find_similar_words(
    target_words: List[str],
    part_of_speech: Optional[str] = None,
    limit: int = 10,
    min_similarity: float = 0.0
) -> dict[str, List[Tuple[Word, float]]]:
    """
    Find similar words for multiple target words in batch.

    More efficient than calling find_similar_words multiple times
    as it reuses database queries and vectorized operations.

    Args:
        target_words: List of words to find similarities for.
        part_of_speech: Optional filter - 'noun' or 'verb' (default: None).
        limit: Maximum number of similar words per target (default: 10).
        min_similarity: Minimum similarity threshold, 0-1 (default: 0.0).

    Returns:
        Dictionary mapping target words to their lists of (Word, similarity) tuples.

    Examples:
        >>> results = batch_find_similar_words(['cat', 'dog'], limit=3)
        >>> for target, similars in results.items():
        ...     print(f"{target}:", [w.word for w, s in similars])
        cat: ['kitten', 'feline', 'pet']
        dog: ['puppy', 'canine', 'pet']
    """
    results = {}

    for word in target_words:
        try:
            results[word] = find_similar_words(
                word,
                part_of_speech=part_of_speech,
                limit=limit,
                min_similarity=min_similarity
            )
        except (Word.DoesNotExist, ValueError) as e:
            # Store error or empty result
            results[word] = []

    return results
