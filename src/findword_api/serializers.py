"""
Serializers for the FindWord API.

This module provides Django REST Framework serializers for converting
Word model instances to/from JSON representations.
"""

from rest_framework import serializers
from .models import Word


class WordSerializer(serializers.ModelSerializer):
    """
    Full serializer for Word model including embedding vector.

    Use this for detailed word retrieval where the embedding vector
    is needed for client-side calculations or analysis.
    """
    embedding_dimension = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = [
            'id',
            'word',
            'is_noun',
            'is_verb',
            'embedding',
            'embedding_dimension',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_embedding_dimension(self, obj):
        """Get the dimension of the embedding vector."""
        if obj.embedding:
            return len(obj.embedding)
        return 0


class WordListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for Word model without embedding vector.

    Use this for list views and search results where the large
    embedding vector would be wasteful to include.
    """
    part_of_speech = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = [
            'id',
            'word',
            'is_noun',
            'is_verb',
            'part_of_speech',
        ]

    def get_part_of_speech(self, obj):
        """Get human-readable part of speech tags."""
        pos = []
        if obj.is_noun:
            pos.append('noun')
        if obj.is_verb:
            pos.append('verb')
        return pos if pos else ['unknown']


class SimilarWordSerializer(serializers.Serializer):
    """
    Serializer for similar word results with similarity score.

    Used in similarity search endpoints to include both the word
    details and its similarity score relative to the target word.
    """
    word = WordListSerializer(read_only=True)
    similarity = serializers.FloatField(
        read_only=True,
        help_text="Cosine similarity score between 0 and 1"
    )

    class Meta:
        fields = ['word', 'similarity']


class SimilaritySearchSerializer(serializers.Serializer):
    """
    Serializer for similarity search request parameters.

    Validates input parameters for the similarity search endpoint.
    """
    pos = serializers.ChoiceField(
        choices=['noun', 'verb'],
        required=False,
        allow_null=True,
        allow_blank=True,
        source='part_of_speech',
        help_text="Filter results by part of speech: 'noun' or 'verb'"
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=100,
        help_text="Maximum number of similar words to return (1-100)"
    )
    min_similarity = serializers.FloatField(
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        help_text="Minimum similarity threshold (0.0-1.0)"
    )

    def validate_part_of_speech(self, value):
        """Normalize part of speech to lowercase and handle empty strings."""
        if value:
            return value.lower()
        return None


class WordSearchSerializer(serializers.Serializer):
    """
    Serializer for word search request parameters.

    Validates input parameters for the word search endpoint.
    """
    q = serializers.CharField(
        required=True,
        min_length=1,
        max_length=100,
        help_text="Search query - word or prefix to search for"
    )
    pos = serializers.ChoiceField(
        choices=['noun', 'verb'],
        required=False,
        allow_null=True,
        allow_blank=True,
        source='part_of_speech',
        help_text="Filter results by part of speech: 'noun' or 'verb'"
    )
    exact = serializers.BooleanField(
        default=False,
        help_text="Whether to search for exact match only (default: prefix search)"
    )

    def validate_part_of_speech(self, value):
        """Normalize part of speech to lowercase and handle empty strings."""
        if value:
            return value.lower()
        return None
