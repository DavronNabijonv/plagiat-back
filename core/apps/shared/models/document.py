from django.db import models

from core.apps.shared.models import BaseModel


class Document(BaseModel):
    title = models.CharField(max_length=200)
    certificate = models.BooleanField(default=False)
    file = models.FileField(null=True, blank=True, upload_to='documents/')
    text = models.TextField(null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='documents')
    
    def __str__(self):
        return self.title
        

class DocumentResult(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='results')
    result_json = models.JSONField()
    