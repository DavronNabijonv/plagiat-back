from django.contrib import admin

from core.apps.shared.models import Document, DocumentResult


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)
    list_filter = ('user',)

@admin.register(DocumentResult)
class DocumentResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'status', 'created_at')
    search_fields = ('document__name',)
