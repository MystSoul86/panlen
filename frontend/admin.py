from django.contrib import admin
from .models import Curso

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_at')
    filter_horizontal = ('moderators', 'members')
    search_fields = ('name', 'description')
    list_filter = ('active', 'created_at')
