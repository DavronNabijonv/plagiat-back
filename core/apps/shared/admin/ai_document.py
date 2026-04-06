from django.contrib import admin

from core.apps.shared.models import AiDocument, AiDocumentResult


admin.site.register(AiDocument)
admin.site.register(AiDocumentResult)
