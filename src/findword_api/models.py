from typing import List, Optional
import numpy as np
from django.db import models
from django.db.models import Q


class Word(models.Model):
    """
    Model for storing word embeddings with part-of-speech tags.

    Stores words along with their vector embeddings for semantic similarity search.
    """
    word = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="The word itself"
    )
    is_noun = models.BooleanField(
        default=False,
        help_text="Whether word can be used as noun"
    )
    is_verb = models.BooleanField(
        default=False,
        help_text="Whether word can be used as verb"
    )
    embedding = models.JSONField(
        help_text="Store embedding vector as JSON array"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when word was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when word was last updated"
    )

    class Meta:
        ordering = ['word']
        verbose_name = 'Word'
        verbose_name_plural = 'Words'
        indexes = [
            models.Index(fields=['word'], name='word_idx'),
            models.Index(fields=['is_noun'], name='noun_idx'),
            models.Index(fields=['is_verb'], name='verb_idx'),
        ]

    def __str__(self) -> str:
        """Return the word as string representation."""
        return self.word

    def get_embedding_array(self) -> np.ndarray:
        """
        Convert the JSON embedding to a numpy array.

        Returns:
            np.ndarray: The embedding vector as numpy array.

        Raises:
            ValueError: If embedding is empty or invalid.
        """
        if not self.embedding:
            raise ValueError(f"Word '{self.word}' has no embedding")

        try:
            return np.array(self.embedding, dtype=np.float32)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid embedding format for word '{self.word}': {e}")

    def cosine_similarity(self, other_word: 'Word') -> float:
        """
        Calculate cosine similarity between this word and another word.

        Args:
            other_word: Another Word instance to compare with.

        Returns:
            float: Cosine similarity score between -1 and 1.

        Raises:
            ValueError: If either word has invalid embeddings.
        """
        if not isinstance(other_word, Word):
            raise TypeError("other_word must be a Word instance")

        vec1 = self.get_embedding_array()
        vec2 = other_word.get_embedding_array()

        if vec1.shape != vec2.shape:
            raise ValueError(
                f"Embedding dimensions don't match: {vec1.shape} vs {vec2.shape}"
            )

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_similar_words(
        self,
        limit: int = 10,
        min_similarity: float = 0.0,
        is_noun: Optional[bool] = None,
        is_verb: Optional[bool] = None
    ) -> List[tuple['Word', float]]:
        """
        Find semantically similar words using cosine similarity.

        Args:
            limit: Maximum number of similar words to return (default: 10).
            min_similarity: Minimum similarity threshold (default: 0.0).
            is_noun: Filter for nouns only if True (default: None, no filter).
            is_verb: Filter for verbs only if True (default: None, no filter).

        Returns:
            List of tuples containing (Word instance, similarity score),
            sorted by similarity in descending order.

        Raises:
            ValueError: If this word has invalid embeddings.
        """
        # Get this word's embedding
        this_embedding = self.get_embedding_array()

        # Build queryset with filters
        queryset = Word.objects.exclude(id=self.id)

        if is_noun is not None:
            queryset = queryset.filter(is_noun=is_noun)
        if is_verb is not None:
            queryset = queryset.filter(is_verb=is_verb)

        # Calculate similarities for all words
        similar_words = []

        for word in queryset:
            try:
                similarity = self.cosine_similarity(word)
                if similarity >= min_similarity:
                    similar_words.append((word, similarity))
            except (ValueError, TypeError):
                # Skip words with invalid embeddings
                continue

        # Sort by similarity (descending) and limit results
        similar_words.sort(key=lambda x: x[1], reverse=True)
        return similar_words[:limit]
