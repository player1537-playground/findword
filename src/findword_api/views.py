"""
API views for the FindWord application.

This module provides REST API endpoints for word retrieval,
similarity search, and word lookup functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import Word
from .serializers import (
    WordSerializer,
    WordListSerializer,
    SimilarWordSerializer,
    SimilaritySearchSerializer,
    WordSearchSerializer,
)
from .similarity import find_similar_words


class WordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Word model providing read-only CRUD operations.

    Endpoints:
    - list: GET /api/words/ - List all words (paginated)
    - retrieve: GET /api/words/{word}/ - Get details of a specific word
    - similar: GET /api/words/{word}/similar/ - Find similar words
    """
    queryset = Word.objects.all()
    lookup_field = 'word'
    lookup_value_regex = '[^/]+'  # Allow any character except /

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'retrieve':
            return WordSerializer
        elif self.action == 'similar':
            return SimilarWordSerializer
        return WordListSerializer

    @extend_schema(
        summary="List all words",
        description="Get paginated list of all words in the database",
        responses={200: WordListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List all words with pagination."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get word details",
        description="Get detailed information about a specific word including its embedding vector",
        responses={
            200: WordSerializer,
            404: {"description": "Word not found"},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific word by its text."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Find similar words",
        description="Find semantically similar words using cosine similarity on word embeddings",
        parameters=[
            OpenApiParameter(
                name='pos',
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by part of speech: 'noun' or 'verb'",
                required=False,
                enum=['noun', 'verb'],
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description="Maximum number of similar words to return (default: 10, max: 100)",
                required=False,
            ),
            OpenApiParameter(
                name='min_similarity',
                type=float,
                location=OpenApiParameter.QUERY,
                description="Minimum similarity threshold 0.0-1.0 (default: 0.0)",
                required=False,
            ),
        ],
        responses={
            200: SimilarWordSerializer(many=True),
            404: {"description": "Word not found"},
            400: {"description": "Invalid parameters"},
        },
        examples=[
            OpenApiExample(
                'Example Response',
                value=[
                    {
                        'word': {
                            'id': 123,
                            'word': 'dog',
                            'is_noun': True,
                            'is_verb': False,
                            'part_of_speech': ['noun']
                        },
                        'similarity': 0.8523
                    },
                    {
                        'word': {
                            'id': 456,
                            'word': 'kitten',
                            'is_noun': True,
                            'is_verb': False,
                            'part_of_speech': ['noun']
                        },
                        'similarity': 0.8234
                    }
                ],
                response_only=True,
            )
        ]
    )
    @action(detail=True, methods=['get'])
    def similar(self, request, word=None):
        """
        Find similar words using semantic similarity search.

        Query parameters:
        - pos: Filter by part of speech ('noun' or 'verb')
        - limit: Maximum number of results (default: 10, max: 100)
        - min_similarity: Minimum similarity threshold (default: 0.0)
        """
        # Validate query parameters
        param_serializer = SimilaritySearchSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response(
                param_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated parameters
        params = param_serializer.validated_data
        part_of_speech = params.get('part_of_speech')
        limit = params.get('limit', 10)
        min_similarity = params.get('min_similarity', 0.0)

        # Find similar words
        try:
            similar_words = find_similar_words(
                target_word=word,
                part_of_speech=part_of_speech,
                limit=limit,
                min_similarity=min_similarity
            )
        except Word.DoesNotExist:
            return Response(
                {'error': f"Word '{word}' not found in database"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Format response
        results = [
            {'word': w, 'similarity': sim}
            for w, sim in similar_words
        ]

        # Serialize and return
        serializer = SimilarWordSerializer(results, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="Search for words",
    description="Search for words by exact match or prefix. Returns paginated results.",
    parameters=[
        OpenApiParameter(
            name='q',
            type=str,
            location=OpenApiParameter.QUERY,
            description="Search query - word or prefix to search for",
            required=True,
        ),
        OpenApiParameter(
            name='pos',
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by part of speech: 'noun' or 'verb'",
            required=False,
            enum=['noun', 'verb'],
        ),
        OpenApiParameter(
            name='exact',
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Whether to search for exact match only (default: false for prefix search)",
            required=False,
        ),
    ],
    responses={
        200: WordListSerializer(many=True),
        400: {"description": "Invalid search query"},
    },
)
@api_view(['GET'])
def search_words(request):
    """
    Search for words by text query.

    Query parameters:
    - q: Search query (required)
    - pos: Filter by part of speech ('noun' or 'verb')
    - exact: If true, search for exact match; otherwise prefix match (default: false)
    """
    # Validate query parameters
    param_serializer = WordSearchSerializer(data=request.query_params)
    if not param_serializer.is_valid():
        return Response(
            param_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # Extract validated parameters
    params = param_serializer.validated_data
    query = params['q']
    part_of_speech = params.get('part_of_speech')
    exact = params.get('exact', False)

    # Build queryset
    if exact:
        queryset = Word.objects.filter(word__iexact=query)
    else:
        queryset = Word.objects.filter(word__istartswith=query)

    # Apply part of speech filter
    if part_of_speech == 'noun':
        queryset = queryset.filter(is_noun=True)
    elif part_of_speech == 'verb':
        queryset = queryset.filter(is_verb=True)

    # Order by word length (shorter first) then alphabetically
    queryset = queryset.order_by('word')

    # Paginate results
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)

    # Serialize results
    serializer = WordListSerializer(page, many=True)

    # Return paginated response
    return paginator.get_paginated_response(serializer.data)


@extend_schema(
    summary="API Root",
    description="Root endpoint providing links to all available API endpoints",
)
@api_view(['GET'])
def api_root(request):
    """
    API root endpoint providing overview and links.
    """
    return Response({
        'message': 'Welcome to the FindWord API',
        'version': '1.0.0',
        'endpoints': {
            'words': '/api/words/',
            'search': '/api/search/',
            'schema': '/api/schema/',
            'docs': '/api/docs/',
        },
        'documentation': 'Visit /api/docs/ for interactive API documentation',
    })
