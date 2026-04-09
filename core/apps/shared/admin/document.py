from django.contrib import admin

from core.apps.shared.models import Document, DocumentResult, DocumentType


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at')
    search_fields = ('title',)
    list_filter = ('user',)

@admin.register(DocumentResult)
class DocumentResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'created_at')
    search_fields = ('document__title',)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('name',)
    list_display_links = ('id', 'name',)
    ordering = ('id',)
