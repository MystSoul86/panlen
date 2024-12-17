from django.urls import path
from . import views

app_name = 'moderator'

urlpatterns = [
    path('dashboard/', views.moderator_dashboard, name='dashboard'),
    path('curso/<int:curso_id>/', views.curso_detail, name='curso_detail'),
    path('curso/<int:curso_id>/students/', views.manage_students, name='manage_students'),
    path('curso/<int:curso_id>/student/<int:student_id>/', views.student_progress, name='student_progress'),
    path('documents/', views.documents_view, name='documents'),
    path('documents/extract-text/', views.extract_text, name='extract_text'),
    path('documents/get-text/', views.get_document_text, name='get_document_text'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
]
