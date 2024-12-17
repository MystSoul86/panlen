import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panlen.settings')
django.setup()

from accounts.models import User

def create_moderator():
    try:
        moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='moderator123',
            first_name='Moderador',
            last_name='Demo',
            user_type='moderator'
        )
        print(f'Usuario moderador creado exitosamente!')
        print(f'Username: moderator')
        print(f'Password: moderator123')
        print(f'Tipo: moderador')
    except Exception as e:
        print(f'Error al crear el moderador: {str(e)}')

if __name__ == '__main__':
    create_moderator()
