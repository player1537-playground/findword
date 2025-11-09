from django.contrib import admin
from .models import Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """Admin interface for Word model."""

    list_display = ['word', 'is_noun', 'is_verb', 'created_at', 'updated_at']
    list_filter = ['is_noun', 'is_verb', 'created_at']
    search_fields = ['word']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['word']

    fieldsets = (
        ('Word Information', {
            'fields': ('word', 'is_noun', 'is_verb')
        }),
        ('Embedding Data', {
            'fields': ('embedding',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
