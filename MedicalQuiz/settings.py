from dotenv import load_dotenv
load_dotenv()
import cloudinary
import cloudinary.uploader
import cloudinary.api
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-only')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')
]



cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', ''),
)
# Application definition
INSTALLED_APPS = [
    'crispy_forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    'django_ckeditor_5',
    'Quizzes',
    'accounts',
    'adminsortable2',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MedicalQuiz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'MedicalQuiz.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Auth Redirects ---
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/Quizzes/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# --- Media ---
MEDIA_URL = 'https://res.cloudinary.com/dudsumkuz/image/upload/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# --- CKEditor ---
CKEDITOR_5_UPLOAD_PATH = "uploads/"
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'link', '|',
            'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
            'alignment', 'bulletedList', 'numberedList', '|',
            'imageUpload', 'blockQuote', 'insertTable', 'mediaEmbed', 'codeBlock', '|',
            'undo', 'redo'
        ],
        'height': 500,
        'width': '100%',
        'image': {
            'toolbar': ['imageTextAlternative', 'toggleImageCaption',
                        'imageStyle:inline', 'imageStyle:block', 'imageStyle:side'],
            'styles': ['inline', 'block', 'side']
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties']
        },
        'fontSize': {
            'options': [10, 12, 14, 16, 18, 20, 22, 24, 'default'],
            'supportAllValues': True
        },
        'fontFamily': {
            'options': ['default', 'Inter, sans-serif', 'Arial, sans-serif',
                        'Georgia, serif', 'Times New Roman, serif'],
            'supportAllValues': True
        },
        'fontColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 0%)', 'label': 'Black'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'Dark Gray'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'Gray'},
                {'color': 'hsl(240, 100%, 50%)', 'label': 'Blue'},
                {'color': 'hsl(0, 75%, 60%)', 'label': 'Red'},
                {'color': 'hsl(120, 60%, 40%)', 'label': 'Green'},
            ]
        },
        'fontBackgroundColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 100%)', 'label': 'White'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'Light Gray'},
                {'color': 'hsl(60, 75%, 85%)', 'label': 'Light Yellow'},
                {'color': 'hsl(0, 75%, 85%)', 'label': 'Light Red'},
                {'color': 'hsl(240, 75%, 85%)', 'label': 'Light Blue'},
            ]
        },
        'alignment': {'options': ['left', 'center', 'right', 'justify']},
        'mediaEmbed': {'previewsInData': True, 'toolbar': ['mediaEmbed']},
    }
}

# --- Stripe (loaded from environment) ---
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

STRIPE_PRICE_3_MONTH = os.environ.get('STRIPE_PRICE_3_MONTH', '')
STRIPE_PRICE_6_MONTH = os.environ.get('STRIPE_PRICE_6_MONTH', '')

# --- Upload Limits ---
DATA_UPLOAD_MAX_NUMBER_FIELDS = 20000
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800

# --- Session ---
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG   # True in production (HTTPS), False locally
SESSION_COOKIE_SAMESITE = 'Lax'

# --- Cloudinary ---
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
}