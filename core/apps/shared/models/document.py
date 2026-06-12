from django.db import models

from core.apps.shared.models import BaseModel


class Document(BaseModel):
    title = models.CharField(max_length=200)
    certificate = models.BooleanField(default=False)
    # BE-07: plagiat bilan birga AI-tekshiruv ham buyurtma qilingan
    ai_check = models.BooleanField(default=False)
    file = models.FileField(null=True, blank=True, upload_to='documents/')
    text = models.TextField(null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='documents')
    certificate_file = models.FileField(null=True, blank=True, upload_to='certificates/')
    type = models.ForeignKey('shared.DocumentType', on_delete=models.SET_NULL, related_name='documents', null=True, blank=True)

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'Hujjat'
        verbose_name_plural = 'Hujjatlar'


class DocumentResult(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='results')
    result_json = models.JSONField()

    def __str__(self):
        return str(self.document.title)

    class Meta:
        verbose_name = 'Hujjat natijasi'
        verbose_name_plural = 'Hujjat natijalari'


class DocumentType(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Hujjat turi'
        verbose_name_plural = 'Hujjat turlari'
