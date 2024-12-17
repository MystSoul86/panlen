from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Count, Avg, Q
from accounts.models import User, Curso
from chatbot.models import ChatSession, ChatMessage
from moderator.models import Document
from django.utils import timezone
from datetime import timedelta
from .forms import CursoForm, UserRegistrationForm

def is_admin(user):
    return user.is_superuser or user.user_type == 'admin'

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.user_type == 'student':
        # Get documents for the student's course with uploader information
        documents = Document.objects.select_related('curso', 'uploaded_by').filter(
            curso__in=request.user.member_courses.all()
        ).order_by('-created_at')  # Order by most recent first
        
        # Get user's courses
        courses = request.user.member_courses.all()
        
        # Add some debug information
        print(f"User courses: {[c.id for c in courses]}")
        print(f"Found documents: {documents.count()}")
        
        return render(request, 'student_dashboard.html', {
            'documents': documents,
            'courses': courses
        })
    elif request.user.user_type == 'moderator':
        return redirect('moderator:dashboard')
        
    # Admin dashboard stats
    try:
        total_documents = Document.objects.count()
        recent_documents = Document.objects.select_related('curso').order_by('-created_at')[:5]
    except:
        total_documents = 0
        recent_documents = []
        
    context = {
        'total_documents': total_documents,
        'total_cursos': Curso.objects.count(),
        'active_chats': ChatSession.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'total_users': User.objects.count(),
        'recent_documents': recent_documents,
        # Removed select_related('curso') since ChatSession doesn't have a curso field
        'recent_chats': ChatSession.objects.select_related('user')
            .annotate(message_count=Count('messages'))
            .order_by('-created_at')[:5]
    }
    return render(request, 'dashboard.html', context)

@login_required
def cursos_view(request):
    if request.user.is_superuser or request.user.user_type == 'admin':
        cursos = Curso.objects.prefetch_related('moderator_documents', 'members', 'moderators').all()
    elif request.user.user_type == 'moderator':
        cursos = request.user.moderated_courses.prefetch_related('moderator_documents', 'members', 'moderators').all()
    else:
        cursos = request.user.member_courses.prefetch_related('moderator_documents', 'members', 'moderators').all()
    
    total_cursos = cursos.count()
    
    # Get active courses (with documents in last 30 days)
    active_cursos = cursos.filter(
        moderator_documents__created_at__gte=timezone.now() - timedelta(days=30)
    ).distinct().count()
    
    context = {
        'cursos': cursos,
        'active_cursos_percent': round((active_cursos / total_cursos * 100) if total_cursos > 0 else 0, 1),
        'avg_documents_per_curso': round(Document.objects.filter(curso__in=cursos).count() / total_cursos if total_cursos > 0 else 0, 1),
        'avg_users_per_curso': round(User.objects.filter(Q(member_courses__in=cursos) | Q(moderated_courses__in=cursos)).distinct().count() / total_cursos if total_cursos > 0 else 0, 1),
    }
    return render(request, 'cursos/cursos.html', context)

@login_required
@user_passes_test(is_admin)
def documents_view(request):
    context = {
        'documents': Document.objects.select_related('curso').order_by('-created_at'),
        'cursos': Curso.objects.all()
    }
    return render(request, 'documents/documents.html', context)

@login_required
@user_passes_test(is_admin)
def chat_view(request):
    current_session = None
    chat_sessions = ChatSession.objects.select_related('user').order_by('-created_at')
    
    if chat_sessions.exists():
        current_session = chat_sessions.first()
    
    context = {
        'chat_sessions': chat_sessions,
        'current_session': current_session,
        'cursos': Curso.objects.all()
    }
    return render(request, 'chat/chat.html', context)

@login_required
@user_passes_test(is_admin)
def new_chat_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        curso_id = request.POST.get('curso')
        
        try:
            curso = Curso.objects.get(id=curso_id)
            chat_session = ChatSession.objects.create(
                title=title,
                curso=curso
            )
            messages.success(request, 'Sesión de chat creada exitosamente')
            return redirect('chat_detail', session_id=chat_session.id)
        except Curso.DoesNotExist:
            messages.error(request, 'El curso seleccionado no existe')
        except Exception as e:
            messages.error(request, f'Error al crear la sesión de chat: {str(e)}')
    
    return redirect('chat')

@login_required
@user_passes_test(is_admin)
def chat_detail_view(request, session_id):
    chat_session = get_object_or_404(ChatSession, id=session_id)
    chat_sessions = ChatSession.objects.select_related('user').order_by('-created_at')
    
    context = {
        'chat_sessions': chat_sessions,
        'current_session': chat_session,
        'cursos': Curso.objects.all()
    }
    return render(request, 'chat/chat.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def create_curso(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name:
            curso = Curso.objects.create(
                name=name,
                description=description
            )
            messages.success(request, 'Curso creado exitosamente.')
            return redirect('cursos')
        else:
            messages.error(request, 'El nombre del curso es requerido.')
    
    return redirect('cursos')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def edit_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name:
            curso.name = name
            curso.description = description
            curso.save()
            messages.success(request, 'Curso actualizado exitosamente.')
        else:
            messages.error(request, 'El nombre del curso es requerido.')
    
    return redirect('cursos')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def toggle_curso_status(request, curso_id):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, id=curso_id)
        curso.active = not curso.active
        curso.save()
        status = "activado" if curso.active else "desactivado"
        messages.success(request, f'Curso {status} exitosamente.')
    return redirect('cursos')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def delete_curso(request, curso_id):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, id=curso_id)
        nombre = curso.name
        curso.delete()
        messages.success(request, f'El curso "{nombre}" ha sido eliminado exitosamente.')
    return redirect('cursos')

@login_required
@user_passes_test(is_admin)
def manage_users_view(request):
    users = User.objects.exclude(id=request.user.id)
    user_form = UserRegistrationForm()
    
    context = {
        'users': users,
        'user_form': user_form,
    }
    
    return render(request, 'manage_users.html', context)

@login_required
@user_passes_test(is_admin)
def edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
            return redirect('manage_users')
    else:
        form = UserRegistrationForm(instance=user)
    
    return render(request, 'edit_user.html', {'form': form, 'user': user})

@login_required
@user_passes_test(is_admin)
def toggle_user_status_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = 'activado' if user.is_active else 'desactivado'
    messages.success(request, f'Usuario {user.username} {status} exitosamente.')
    return redirect('manage_users')

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def create_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'Usuario "{user.username}" creado exitosamente.')
            return redirect('manage_users')
        else:
            messages.error(request, 'Error al crear el usuario. Por favor, verifica los datos.')
    return redirect('manage_users')

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user != request.user:  # Prevent self-deletion
            username = user.username
            user.delete()
            messages.success(request, f'Usuario "{username}" eliminado exitosamente.')
        else:
            messages.error(request, 'No puedes eliminar tu propio usuario.')
    return redirect('manage_users')

@login_required
@user_passes_test(is_admin)
def change_user_role(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        if new_role in ['admin', 'moderator', 'student']:
            user.user_type = new_role
            user.save()
            messages.success(request, f'Rol de usuario actualizado a {new_role}.')
        else:
            messages.error(request, 'Rol inválido.')
    return redirect('manage_users')

@login_required
@user_passes_test(is_admin)
def change_user_password(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Contraseña actualizada exitosamente.')
        else:
            messages.error(request, 'La contraseña no puede estar vacía.')
    return redirect('manage_users')

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_roles_view(request):
    context = {
        'students': User.objects.filter(user_type='student'),
        'teachers': User.objects.filter(user_type='moderator'),
        'cursos': Curso.objects.all()
    }
    return render(request, 'manage_roles.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def manage_curso_members(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    available_teachers = User.objects.filter(user_type='moderator')
    available_students = User.objects.filter(user_type='student')
    
    context = {
        'curso': curso,
        'available_teachers': available_teachers,
        'available_students': available_students,
    }
    
    return render(request, 'cursos/manage_members.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def assign_curso_moderators(request, curso_id):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, id=curso_id)
        moderator_ids = request.POST.getlist('moderators')
        
        # Actualizar moderadores
        curso.moderators.clear()
        if moderator_ids:
            curso.moderators.add(*User.objects.filter(id__in=moderator_ids))
        
        messages.success(request, 'Profesores asignados exitosamente.')
    
    return redirect('manage_curso_members', curso_id=curso_id)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def assign_curso_students(request, curso_id):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, id=curso_id)
        student_ids = request.POST.getlist('students')
        
        # Actualizar estudiantes
        curso.members.clear()
        if student_ids:
            curso.members.add(*User.objects.filter(id__in=student_ids))
        
        messages.success(request, 'Estudiantes asignados exitosamente.')
    
    return redirect('manage_curso_members', curso_id=curso_id)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.user_type == 'admin')
def profile_view(request):
    curso_form = CursoForm()
    user_form = UserRegistrationForm() if request.user.user_type == 'admin' else None
    
    if request.method == 'POST':
        if 'create_curso' in request.POST:
            curso_form = CursoForm(request.POST)
            if curso_form.is_valid():
                curso = curso_form.save(commit=False)
                curso.save()
                curso.moderators.add(request.user)
                messages.success(request, 'Curso creado exitosamente')
                return redirect('profile')
            else:
                messages.error(request, 'Error al crear el curso')
        elif 'register_user' in request.POST and request.user.user_type == 'admin':
            user_form = UserRegistrationForm(request.POST)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                messages.success(request, 'Usuario registrado exitosamente')
                return redirect('profile')
            else:
                messages.error(request, 'Error al registrar usuario')
        else:
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password:
                if new_password == confirm_password:
                    user.set_password(new_password)
                    messages.success(request, 'Contraseña actualizada exitosamente')
                else:
                    messages.error(request, 'Las contraseñas no coinciden')
                    return render(request, 'profile.html', {
                        'user': user,
                        'curso_form': curso_form,
                        'user_form': user_form
                    })
            
            try:
                user.save()
                messages.success(request, 'Perfil actualizado exitosamente')
                
                if new_password:
                    login(request, user)
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar el perfil: {str(e)}')
    
    users = User.objects.all() if request.user.user_type == 'admin' else None
    
    return render(request, 'profile.html', {
        'user': request.user,
        'curso_form': curso_form,
        'user_form': user_form,
        'users': users
    })
