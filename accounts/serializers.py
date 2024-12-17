from rest_framework import serializers
from .models import User, Curso

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'user_type', 'first_name', 'last_name')
        read_only_fields = ('id',)

class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ('id', 'name', 'description', 'moderators', 'members', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
