from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create default admin superuser'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@beta24.in',
                password='admin123'
            )
            self.stdout.write('Superuser created: admin / admin123')
        else:
            self.stdout.write('Superuser already exists')