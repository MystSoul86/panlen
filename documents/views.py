from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from moderator.models import Document
from .serializers import DocumentSerializer
from .services import DocumentService
import PyPDF2
import docx
import io

# Create your views here.

class IsModeratorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_type in ['moderator', 'admin']

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsModeratorOrAdmin]

    def get_queryset(self):
        """Filter documents by group"""
        user = self.request.user
        if user.user_type == 'admin':
            return Document.objects.all()
        return Document.objects.filter(group__in=user.moderated_groups.all())

    def create(self, request, *args, **kwargs):
        """Handle document upload and processing"""
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        title = request.data.get('title', file_obj.name)
        group_id = request.data.get('group')
        
        if not group_id:
            return Response(
                {'error': 'Group ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = DocumentService()
            document = service.process_document(
                file_obj=file_obj,
                title=title,
                group_id=group_id,
                user=request.user
            )
            
            serializer = self.get_serializer(document)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
