from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'beta24-secret-key-change-in-production-xyz123'
DEBUG = True
ALLOWED_HOSTS = ['*']

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'riders',
    'tasks',
    'payouts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
     'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'beta24.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'beta24.wsgi.application'

# SQLite (easy setup, can switch to MySQL later)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'beta24.db',
#     }
# }

# MySQL (uncomment & configure when ready)
# 
DATABASE_URL = os.environ.get('DATABASE_URL')  # Get the database URL from environment variable

if DATABASE_URL:
    # Render pe PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    # Local pe MySQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'beta24',
            'USER': 'root',
            'PASSWORD': 'root',   # apna MySQL password
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_DIR = BASE_DIR / 'static'
STATICFILES_DIRS = [STATIC_DIR] if STATIC_DIR.exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
# Auto-create superuser on first deploy
# Auto-create superuser on first deploy

if os.environ.get('DATABASE_URL'):
    try:
        import django
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@beta24.in', 'admin123')
            print('Superuser created: admin / admin123')
    except Exception as e:
        print(f'Superuser creation skipped: {e}')