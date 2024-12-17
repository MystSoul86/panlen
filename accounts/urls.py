from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'cursos', views.CursoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', views.login_view, name='login'),
    path('register/student/', views.register_student_view, name='register_student'),
    path('register/teacher/', views.register_teacher_view, name='register_teacher'),
    path('users/', views.manage_roles_view, name='manage_roles'),
]
