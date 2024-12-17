import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panlen.settings')
django.setup()

from frontend.models import Curso
from accounts.models import User

def create_demo_course():
    try:
        # Obtener el usuario moderador
        moderator = User.objects.get(username='moderator')
        
        # Crear un curso de ejemplo
        curso = Curso.objects.create(
            name='Curso Demo',
            description='Este es un curso de demostración para probar la aplicación.',
            active=True
        )
        
        # Asignar el moderador al curso
        curso.moderators.add(moderator)
        
        print(f'Curso demo creado exitosamente!')
        print(f'Nombre: {curso.name}')
        print(f'ID: {curso.id}')
        print(f'Moderador asignado: {moderator.username}')
    except Exception as e:
        print(f'Error al crear el curso: {str(e)}')

if __name__ == '__main__':
    create_demo_course()
