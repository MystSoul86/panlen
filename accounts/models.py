from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Estudiante'),
        ('moderator', 'Profesor'),
        ('admin', 'Administrador'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    specialization = models.CharField(max_length=100, blank=True, null=True, help_text='Especialización del profesor')
    
    class Meta:
        db_table = 'users'

class Curso(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    moderators = models.ManyToManyField(User, related_name='moderated_courses')
    members = models.ManyToManyField(User, related_name='member_courses')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cursos'

    def __str__(self):
        return self.name
