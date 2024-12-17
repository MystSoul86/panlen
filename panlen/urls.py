"""
URL configuration for panlen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from frontend import views as frontend_views
from accounts import views as account_views
from django.views.generic import RedirectView
from chatbot import views as chatbot_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include('accounts.urls')),
    path('api/chat/send/', chatbot_views.send_message, name='chat_send'),
    path('api/documents/', include('documents.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    
    # Frontend URLs
    path('', frontend_views.dashboard, name='dashboard'),
    path('login/', frontend_views.login_view, name='login'),
    path('logout/', frontend_views.logout_view, name='logout'),
    path('cursos/', frontend_views.cursos_view, name='cursos'),
    path('cursos/create/', frontend_views.create_curso, name='create_curso'),
    path('cursos/<int:curso_id>/edit/', frontend_views.edit_curso, name='edit_curso'),
    path('cursos/<int:curso_id>/delete/', frontend_views.delete_curso, name='delete_curso'),
    path('cursos/<int:curso_id>/toggle_status/', frontend_views.toggle_curso_status, name='toggle_curso_status'),
    path('cursos/<int:curso_id>/members/', frontend_views.manage_curso_members, name='manage_curso_members'),
    path('cursos/<int:curso_id>/members/moderators/', frontend_views.assign_curso_moderators, name='assign_curso_moderators'),
    path('cursos/<int:curso_id>/members/students/', frontend_views.assign_curso_students, name='assign_curso_students'),
    path('documents/', frontend_views.documents_view, name='documents'),
   
    path('profile/', frontend_views.profile_view, name='profile'),
    path('manage-users/', frontend_views.manage_users_view, name='manage_users'),
    path('users/<int:user_id>/delete/', frontend_views.delete_user, name='delete_user'),
    path('users/<int:user_id>/change-role/', frontend_views.change_user_role, name='change_user_role'),
    path('users/<int:user_id>/change-password/', frontend_views.change_user_password, name='change_user_password'),
    path('users/create/', frontend_views.create_user, name='create_user'),
    
    # Role Management URLs
    path('roles/manage/', account_views.manage_roles_view, name='manage_roles'),
    path('roles/register/student/', account_views.register_student_view, name='register_student'),
    path('roles/register/teacher/', account_views.register_teacher_view, name='register_teacher'),
    path('roles/assign/student/<int:student_id>/', account_views.assign_student_courses, name='assign_student_courses'),
    path('roles/assign/teacher/<int:teacher_id>/', account_views.assign_teacher_courses, name='assign_teacher_courses'),
    
    # Moderator URLs
    path('moderator/', include('moderator.urls', namespace='moderator')),
    
    # Chatbot URLs
    path('chatbot/', include('chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
