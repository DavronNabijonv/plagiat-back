from django.db import models

from core.apps.shared.models import BaseModel


class AiDocument(BaseModel):
    title = models.CharField(max_length=255, null=True)
    file = models.FileField(upload_to='ai_documents/')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='ai_documents')
    total_words = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Document {self.id} by {self.user}"

    class Meta:
        verbose_name = 'SI Detektor'
        verbose_name_plural = 'SI Detektorlar'


class AiDocumentResult(BaseModel):
    document = models.OneToOneField(AiDocument, on_delete=models.CASCADE, related_name='result')
    result = models.JSONField()

    def __str__(self):
        return f"Result for {self.document}"
