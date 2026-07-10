import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beta24.settings')
django.setup()

from django.contrib.auth.models import User

username = 'beta24'
password = 'Betaa24'
email = 'admin@beta24.in'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password, email=email)
    print(f'Superuser created: {username} / {password}')
else:
    print('Superuser already exists')