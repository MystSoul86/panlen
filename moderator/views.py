from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import User, Curso
from django.db.models import Q, Prefetch
from moderator.models import Document
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import UploadedFile
from documents.services import DocumentService
import PyPDF2
import docx
import io
from chatbot.models import ChatSession, ChatMessage

def is_moderator(user):
    return user.user_type == 'moderator'

@login_required
@user_passes_test(is_moderator)
def moderator_dashboard(request):
    # Obtener cursos donde el usuario es moderador con prefetch de miembros
    cursos = Curso.objects.filter(
        moderators=request.user
    ).prefetch_related(
        Prefetch(
            'members',
            queryset=User.objects.all().order_by('first_name', 'last_name')
        )
    ).order_by('name')
    
    # Debug information
    print(f"Usuario: {request.user.username}")
    print(f"Tipo de usuario: {request.user.user_type}")
    print(f"Número de cursos encontrados: {cursos.count()}")
    for curso in cursos:
        print(f"Curso: {curso.name}")
        print(f"Estudiantes: {curso.members.count()}")
        for student in curso.members.all():
            print(f"  - {student.get_full_name()} ({student.username})")
    
    context = {
        'cursos': cursos,
    }
    return render(request, 'moderator/dashboard.html', context)

@login_required
@user_passes_test(is_moderator)
def curso_detail(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id, moderators=request.user)
    students = curso.members.all()
    
    context = {
        'curso': curso,
        'students': students,
    }
    return render(request, 'moderator/curso_detail.html', context)

@login_required
@user_passes_test(is_moderator)
def manage_students(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id, moderators=request.user)
    students = curso.members.all()
    
    if request.method == 'POST':
        # Aquí puedes agregar lógica para calificar estudiantes o tomar asistencia
        pass
    
    context = {
        'curso': curso,
        'students': students,
    }
    return render(request, 'moderator/manage_students.html', context)

@login_required
@user_passes_test(is_moderator)
def student_progress(request, curso_id, student_id):
    curso = get_object_or_404(Curso, id=curso_id, moderators=request.user)
    student = get_object_or_404(User, id=student_id, user_type='student')
    
    # Get chat sessions and messages for this student
    chat_sessions = ChatSession.objects.filter(user=student).order_by('-created_at')
    chat_history = []
    
    for session in chat_sessions:
        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        chat_history.append({
            'session': session,
            'messages': messages,
            'message_count': messages.count()
        })
    
    context = {
        'curso': curso,
        'student': student,
        'chat_history': chat_history,
    }
    return render(request, 'moderator/student_progress.html', context)

@login_required
@user_passes_test(is_moderator)
def documents_view(request):
    # Obtener los cursos del moderador
    cursos = Curso.objects.filter(moderators=request.user)
    # Obtener los documentos del moderador
    documents = Document.objects.filter(
        curso__in=cursos
    ).select_related('curso', 'uploaded_by').order_by('-created_at')
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            curso_id = request.POST.get('curso')
            file = request.FILES.get('file')
            
            if not all([title, curso_id, file]):
                messages.error(request, 'Por favor complete todos los campos.')
                return redirect('moderator:documents')
            
            # Verificar que el curso pertenece al moderador
            curso = get_object_or_404(Curso, id=curso_id, moderators=request.user)
            
            # Usar DocumentService para procesar el documento
            document_service = DocumentService()
            document = document_service.process_document(
                file_obj=file,
                title=title,
                group=curso,
                user=request.user
            )
            
            messages.success(request, f'Documento "{title}" subido exitosamente.')
            return redirect('moderator:documents')
            
        except Exception as e:
            messages.error(request, f'Error al subir el documento: {str(e)}')
            return redirect('moderator:documents')
    
    context = {
        'cursos': cursos,
        'documents': documents,
    }
    return render(request, 'moderator/documents.html', context)

@login_required
@user_passes_test(is_moderator)
def delete_document(request, document_id):
    try:
        document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
        title = document.title
        document.delete()
        messages.success(request, f'Documento "{title}" eliminado exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el documento: {str(e)}')
    
    return redirect('moderator:documents')

@login_required
@require_http_methods(["POST"])
def extract_text(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file: UploadedFile = request.FILES['file']
    text = ''
    
    try:
        # Extraer texto según el tipo de archivo
        if file.name.endswith('.pdf'):
            # PDF
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
        
        elif file.name.endswith('.docx'):
            # Word
            doc = docx.Document(file)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        elif file.name.endswith('.txt'):
            # Texto plano
            text = file.read().decode('utf-8')
        
        else:
            return JsonResponse({'error': 'Formato de archivo no soportado'}, status=400)
        
        return JsonResponse({'text': text})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_document_text(request):
    try:
        document_id = request.GET.get('document_id')
        if not document_id:
            return JsonResponse({'error': 'No document ID provided'}, status=400)
        
        document = Document.objects.get(id=document_id)
        
        # Verificar que el usuario tenga acceso al documento
        if not (request.user.is_superuser or 
                request.user.user_type == 'admin' or
                document.curso in request.user.moderated_courses.all() or
                document.curso in request.user.member_courses.all()):
            return JsonResponse({'error': 'No tiene permiso para ver este documento'}, status=403)
        
        return JsonResponse({'text': document.content_text})
    
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Documento no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
