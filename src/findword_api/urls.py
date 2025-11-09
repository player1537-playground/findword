"""
URL configuration for the FindWord API.

This module defines all API endpoints including word retrieval,
similarity search, and documentation endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

app_name = 'findword_api'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'words', views.WordViewSet, basename='word')

urlpatterns = [
    # API root
    path('', views.api_root, name='api-root'),

    # ViewSet routes (includes list, retrieve, and custom actions)
    path('', include(router.urls)),

    # Search endpoint
    path('search/', views.search_words, name='search'),

    # OpenAPI schema and documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='findword_api:schema'), name='docs'),
]
