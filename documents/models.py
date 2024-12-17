from django.db import models
from accounts.models import Curso, User


# class Document(models.Model):
#     title = models.CharField(max_length=200)
#     file = models.FileField(upload_to='documents/')
#     curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='documents', null=True)
#     uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     content_text = models.TextField(blank=True)  # Stored text content for context

#     class Meta:
#         db_table = 'moderator_document'

#     def __str__(self):
#         return self.title


