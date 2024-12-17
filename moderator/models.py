from django.db import models
from django.conf import settings
from accounts.models import Curso

# Create your models here.

class Document(models.Model):
    title = models.CharField(max_length=255, verbose_name='Título')
    file = models.FileField(upload_to='documents/', verbose_name='Archivo')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='moderator_documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderator_uploaded_documents')
    content_text = models.TextField(null=True, blank=True, verbose_name='Contenido del texto')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
