from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate, login
from .models import User, Curso
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, CursoSerializer
import logging

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_superuser or user.user_type == 'admin'

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and is_admin(request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        if is_admin(self.request.user):
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def perform_create(self, serializer):
        user = serializer.save()
        if 'password' in self.request.data:
            user.set_password(self.request.data['password'])
            user.save()

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if is_admin(self.request.user):
            return Curso.objects.all()
        elif self.request.user.user_type == 'teacher':
            return Curso.objects.filter(moderated_courses=self.request.user)
        else:
            return Curso.objects.filter(member_courses=self.request.user)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        curso = self.get_object()
        curso.members.add(request.user)
        return Response({'status': 'joined'})

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        curso = self.get_object()
        curso.members.remove(request.user)
        return Response({'status': 'left'})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.user_type == 'moderator':
                return redirect('moderator:dashboard')
            return redirect('dashboard')  # Redirigir al dashboard principal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'login.html')

@login_required
@user_passes_test(is_admin)
@csrf_protect
def register_student_view(request):
    if request.method == 'POST':
        try:
            # Log the POST data
            logger.info("POST data received:")
            for key, value in request.POST.items():
                logger.info(f"{key}: {value}")
            
            # Extract form data
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            user_type = request.POST.get('user_type', 'student')
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name]):
                missing_fields = []
                if not username: missing_fields.append('username')
                if not email: missing_fields.append('email')
                if not password: missing_fields.append('password')
                if not first_name: missing_fields.append('first_name')
                if not last_name: missing_fields.append('last_name')
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                raise ValueError(f"Username {username} already exists")
            
            if User.objects.filter(email=email).exists():
                raise ValueError(f"Email {email} already exists")
            
            # Create user
            logger.info(f"Creating user with username: {username}, email: {email}, type: {user_type}")
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type
            )
            
            user_type_display = {
                'student': 'Estudiante',
                'moderator': 'Profesor',
                'admin': 'Administrador'
            }
            
            messages.success(request, f'{user_type_display[user_type]} {username} registrado exitosamente.')
            logger.info(f"User created successfully: {username}")
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            messages.error(request, f'Error al registrar usuario: {str(e)}')
        
    return redirect('/manage-users/')

@login_required
@user_passes_test(is_admin)
@csrf_protect
def register_teacher_view(request):
    if request.method == 'POST':
        try:
            # Extract form data
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            specialization = request.POST.get('specialization', '').strip()
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name]):
                missing_fields = []
                if not username: missing_fields.append('username')
                if not email: missing_fields.append('email')
                if not password: missing_fields.append('password')
                if not first_name: missing_fields.append('first_name')
                if not last_name: missing_fields.append('last_name')
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                raise ValueError(f"Username {username} already exists")
            
            if User.objects.filter(email=email).exists():
                raise ValueError(f"Email {email} already exists")
            
            # Create user
            logger.info(f"Creating teacher user with username: {username}, email: {email}")
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type='teacher',
                specialization=specialization
            )
            messages.success(request, f'Profesor {username} registrado exitosamente.')
            logger.info(f"Teacher user created successfully: {username}")
            
        except Exception as e:
            logger.error(f"Error creating teacher user: {str(e)}")
            messages.error(request, f'Error al registrar profesor: {str(e)}')
        
    return redirect('manage_roles')

@login_required
@user_passes_test(is_admin)
def manage_roles_view(request):
    context = {
        'users': User.objects.all().order_by('user_type', 'username'),
        'cursos': Curso.objects.all()
    }
    return render(request, 'manage_users.html', context)

@login_required
@user_passes_test(is_admin)
@csrf_protect
def register_student(request):
    if request.method == 'POST':
        try:
            # Extract form data
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name]):
                missing_fields = []
                if not username: missing_fields.append('username')
                if not email: missing_fields.append('email')
                if not password: missing_fields.append('password')
                if not first_name: missing_fields.append('first_name')
                if not last_name: missing_fields.append('last_name')
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                raise ValueError(f"Username {username} already exists")
            
            if User.objects.filter(email=email).exists():
                raise ValueError(f"Email {email} already exists")
            
            # Create student user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type='student'  # Explicitly set as student
            )
            messages.success(request, f'Estudiante {username} registrado exitosamente.')
            logger.info(f"Student user created successfully: {username}")
            
        except Exception as e:
            logger.error(f"Error creating student user: {str(e)}")
            messages.error(request, f'Error al registrar estudiante: {str(e)}')
        
    return redirect('manage_roles')

@login_required
@user_passes_test(is_admin)
@csrf_protect
def register_teacher(request):
    if request.method == 'POST':
        try:
            # Extract form data
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            specialization = request.POST.get('specialization', '').strip()
            
            # Validate required fields
            if not all([username, email, password, first_name, last_name]):
                missing_fields = []
                if not username: missing_fields.append('username')
                if not email: missing_fields.append('email')
                if not password: missing_fields.append('password')
                if not first_name: missing_fields.append('first_name')
                if not last_name: missing_fields.append('last_name')
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                raise ValueError(f"Username {username} already exists")
            
            if User.objects.filter(email=email).exists():
                raise ValueError(f"Email {email} already exists")
            
            # Create teacher user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type='teacher',  # Explicitly set as teacher
                specialization=specialization
            )
            messages.success(request, f'Profesor {username} registrado exitosamente.')
            logger.info(f"Teacher user created successfully: {username}")
            
        except Exception as e:
            logger.error(f"Error creating teacher user: {str(e)}")
            messages.error(request, f'Error al registrar profesor: {str(e)}')
        
    return redirect('manage_roles')

@login_required
@user_passes_test(is_admin)
@csrf_protect
def create_curso(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            
            if not nombre:
                raise ValueError("El nombre del curso es requerido")
            
            curso = Curso.objects.create(
                name=nombre,
                description=descripcion,
                active=True
            )
            messages.success(request, f'Curso "{nombre}" creado exitosamente.')
            logger.info(f"Course created successfully: {nombre}")
            
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            messages.error(request, f'Error al crear curso: {str(e)}')
    
    return redirect('cursos')

@login_required
@user_passes_test(is_admin)
@csrf_protect
def edit_curso(request, curso_id):
    if request.method == 'POST':
        try:
            curso = get_object_or_404(Curso, id=curso_id)
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            
            if not nombre:
                raise ValueError("El nombre del curso es requerido")
            
            curso.name = nombre
            curso.description = descripcion
            curso.save()
            
            messages.success(request, f'Curso "{nombre}" actualizado exitosamente.')
            logger.info(f"Course updated successfully: {nombre}")
            
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            messages.error(request, f'Error al actualizar curso: {str(e)}')
    
    return redirect('cursos')

@login_required
@user_passes_test(is_admin)
def toggle_curso_status(request, curso_id):
    if request.method == 'POST':
        try:
            curso = get_object_or_404(Curso, id=curso_id)
            action = request.POST.get('action')
            
            if action == 'activate':
                curso.active = True
                status_msg = 'activado'
            else:
                curso.active = False
                status_msg = 'desactivado'
            
            curso.save()
            messages.success(request, f'Curso "{curso.name}" {status_msg} exitosamente.')
            logger.info(f"Course status updated: {curso.name} - {status_msg}")
            
        except Exception as e:
            logger.error(f"Error toggling course status: {str(e)}")
            messages.error(request, f'Error al cambiar estado del curso: {str(e)}')
    
    return redirect('cursos')

@login_required
def cursos_view(request):
    cursos = Curso.objects.all()
    return render(request, 'cursos/cursos.html', {'cursos': cursos})

@login_required
@user_passes_test(is_admin)
def assign_student_courses(request, student_id):
    if request.method == 'POST':
        try:
            student = get_object_or_404(User, id=student_id, user_type='student')
            course_ids = request.POST.getlist('courses')
            
            # Clear existing courses and add new ones
            student.member_courses.clear()
            for course_id in course_ids:
                curso = get_object_or_404(Curso, id=course_id)
                student.member_courses.add(curso)
            
            messages.success(request, f'Cursos asignados exitosamente a {student.username}')
            logger.info(f"Courses assigned to student {student.username}: {course_ids}")
            
        except Exception as e:
            logger.error(f"Error assigning courses to student: {str(e)}")
            messages.error(request, f'Error al asignar cursos: {str(e)}')
    
    return redirect('manage_roles')

@login_required
@user_passes_test(is_admin)
def assign_teacher_courses(request, teacher_id):
    if request.method == 'POST':
        try:
            teacher = get_object_or_404(User, id=teacher_id, user_type='teacher')
            course_ids = request.POST.getlist('courses')
            
            # Clear existing courses and add new ones
            teacher.moderated_courses.clear()
            for course_id in course_ids:
                curso = get_object_or_404(Curso, id=course_id)
                teacher.moderated_courses.add(curso)
            
            messages.success(request, f'Cursos asignados exitosamente a {teacher.username}')
            logger.info(f"Courses assigned to teacher {teacher.username}: {course_ids}")
            
        except Exception as e:
            logger.error(f"Error assigning courses to teacher: {str(e)}")
            messages.error(request, f'Error al asignar cursos: {str(e)}')
    
    return redirect('manage_roles')
