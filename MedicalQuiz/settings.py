from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-fpx$wjkw8kq$=3izs&0o*k6oi7c+kp7)b@4=9)3%u)9+gecyv6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "frcophth-pro-eu.onrender.com",
    "frcophth-pro.onrender.com",
    "localhost",
    "127.0.0.1"
]

# Application definition

INSTALLED_APPS = [
    'crispy_forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
        'DIRS': [BASE_DIR / "templates"],
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


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}




#DATABASES = {
#    'default': dj_database_url.config(
#        default=os.environ.get('DATABASE_URL'),
###        conn_max_age=600,
#        ssl_require=True
#    )
#}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR, 'templates')]


STATIC_URL = 'static/'
STATICFILES_DIRS = [ BASE_DIR / 'static' ]


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"



LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/Quizzes/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


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
            'toolbar': [
                'imageTextAlternative', 
                'toggleImageCaption', 
                'imageStyle:inline', 
                'imageStyle:block', 
                'imageStyle:side'
            ],
            'styles': ['inline', 'block', 'side']
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 
                'tableRow', 
                'mergeTableCells', 
                'tableProperties', 
                'tableCellProperties'
            ]
        },
        'fontSize': {
            'options': [10, 12, 14, 16, 18, 20, 22, 24, 'default'],
            'supportAllValues': True
        },
        'fontFamily': {
            'options': [
                'default',
                'Inter, sans-serif',
                'Arial, sans-serif',
                'Georgia, serif',
                'Times New Roman, serif'
            ],
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
        'alignment': {
            'options': ['left', 'center', 'right', 'justify']
        },
        'mediaEmbed': {
            'previewsInData': True,
            'toolbar': ['mediaEmbed']
        },
    }
}


STRIPE_PUBLIC_KEY = "pk_test_51SM2rYKPRXR2L86t8fE3oUdnwnJe0au8nYCXTmLbsP4J59ZHfV4LLqD07rXXEpH5F64b290x8OyOXPJNyOgp7P9l00TvrXKH9n"
STRIPE_SECRET_KEY = "sk_test_51SM2rYKPRXR2L86ty7hl9He10sz33WQOY06GYGTkfoA3o7mI9WTmPgG3srdihPAONe24kfeNtVXbQiGdOO3tqDLI00piX0JpnU"
STRIPE_WEBHOOK_SECRET = ""