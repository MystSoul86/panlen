from rest_framework import serializers
from moderator.models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'file', 'curso', 'uploaded_by', 'created_at', 'updated_at', 'content_text')
        read_only_fields = ('id', 'created_at', 'updated_at', 'content_text')
