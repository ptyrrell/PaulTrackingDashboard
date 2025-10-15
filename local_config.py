# Local development configuration
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = os.path.dirname(__file__)

# Enable debug for development
DEBUG = True

# Database configuration - using SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'db.sqlite3'),
    }
}

# Static files configuration
STATIC_ROOT = os.path.join(PROJECT_DIR, 'staticfiles')

# Disable email sending for local development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable ReCaptcha for local development  
RE_CAPTCHA_ENABLED = False
