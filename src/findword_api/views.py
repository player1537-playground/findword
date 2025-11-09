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
from django.shortcuts import render
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
import io
import numpy as np

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
        summary="Visualize word semantic space",
        description="Generate a t-SNE visualization of the semantic space around a target word",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of similar words to include in visualization (default: 15, max: 50)",
                required=False,
            ),
        ],
        responses={
            200: {
                'description': 'PNG image of the t-SNE visualization',
                'content': {'image/png': {}},
            },
            404: {"description": "Word not found"},
            400: {"description": "Invalid parameters or visualization error"},
        },
    )
    @action(detail=True, methods=['get'], url_path='visualize')
    def visualize(self, request, word=None):
        """
        Generate a t-SNE visualization of the word and its similar words.

        Query parameters:
        - limit: Number of similar words to include (default: 15, max: 50)
        """
        try:
            # Validate limit parameter
            try:
                limit = int(request.query_params.get('limit', 15))
                limit = min(max(limit, 1), 50)
            except (ValueError, TypeError):
                limit = 15

            # Get the target word
            target_word = Word.objects.get(word__iexact=word)

            # Find similar words
            similar_words = target_word.get_similar_words(limit=limit)

            # Collect embeddings for visualization
            words_to_plot = [target_word] + [w for w, _ in similar_words]
            embeddings = np.array([w.get_embedding_array() for w in words_to_plot])

            # Apply PCA for dimensionality reduction
            try:
                from sklearn.decomposition import PCA

                # Reduce to reasonable dimensions before t-SNE
                pca = PCA(n_components=min(8, embeddings.shape[1]))
                embeddings_reduced = pca.fit_transform(embeddings)
            except ImportError:
                embeddings_reduced = embeddings

            # Apply t-SNE for 2D visualization
            try:
                from sklearn.manifold import TSNE

                tsne = TSNE(
                    n_components=2,
                    random_state=42,
                    perplexity=min(30, len(words_to_plot) - 1),
                    n_iter=1000,
                )
                embeddings_2d = tsne.fit_transform(embeddings_reduced)
            except ImportError:
                # Fallback: just use PCA if t-SNE not available
                from sklearn.decomposition import PCA
                pca = PCA(n_components=2)
                embeddings_2d = pca.fit_transform(embeddings_reduced)

            # Create visualization
            try:
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend
                import matplotlib.pyplot as plt

                fig, ax = plt.subplots(figsize=(12, 10), dpi=100)

                # Plot similar words
                for i in range(1, len(embeddings_2d)):
                    x, y = embeddings_2d[i]
                    word_obj = words_to_plot[i]
                    pos = ['noun' if word_obj.is_noun else '', 'verb' if word_obj.is_verb else '']
                    pos = ' '.join(filter(bool, pos)) or 'other'

                    # Color based on part of speech
                    if word_obj.is_noun:
                        color = '#667eea'  # Blue for nouns
                    elif word_obj.is_verb:
                        color = '#764ba2'  # Purple for verbs
                    else:
                        color = '#999'  # Gray for others

                    ax.scatter(x, y, s=300, alpha=0.7, color=color)
                    ax.annotate(word_obj.word, (x, y), fontsize=9, ha='center', va='center')

                # Plot target word (larger)
                target_x, target_y = embeddings_2d[0]
                ax.scatter(target_x, target_y, s=600, color='#ff6b6b', marker='*',
                          edgecolors='#c92a2a', linewidths=2, zorder=5)
                ax.annotate(target_word.word, (target_x, target_y), fontsize=12,
                           ha='center', va='center', fontweight='bold')

                # Styling
                ax.set_xlabel('Semantic Dimension 1', fontsize=11, fontweight='bold')
                ax.set_ylabel('Semantic Dimension 2', fontsize=11, fontweight='bold')
                ax.set_title(f'Semantic Space: "{target_word.word}" and Similar Words',
                            fontsize=14, fontweight='bold', pad=20)
                ax.grid(True, alpha=0.3)

                # Add legend
                from matplotlib.patches import Patch
                legend_elements = [
                    Patch(facecolor='#ff6b6b', label='Target word'),
                    Patch(facecolor='#667eea', label='Noun'),
                    Patch(facecolor='#764ba2', label='Verb'),
                    Patch(facecolor='#999', label='Other'),
                ]
                ax.legend(handles=legend_elements, loc='best', fontsize=10)

                # Save to buffer
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                buf.seek(0)
                plt.close(fig)

                # Return as image
                return HttpResponse(buf.getvalue(), content_type='image/png')

            except ImportError:
                return Response(
                    {'error': 'Visualization requires matplotlib and scikit-learn to be installed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Visualization generation failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Word.DoesNotExist:
            return Response(
                {'error': f"Word '{word}' not found in database"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error generating visualization: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


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


def index(request):
    """
    Render the main FindWord web interface.

    GET /:
        Returns HTML page with search interface and visualization features.
    """
    return render(request, 'findword_api/index.html')
