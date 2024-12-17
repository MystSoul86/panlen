from django.db import models
from accounts.models import User

class Curso(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    moderators = models.ManyToManyField(User, related_name='cursos_moderados')
    members = models.ManyToManyField(User, related_name='cursos_inscritos')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-created_at']
