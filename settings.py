# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.core.urlresolvers import reverse_lazy

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = os.path.dirname(__file__)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'jzta&pmo9spn5oyq=g1=pjm1bj1fl=#o^t#huts717*)xpt#7e'

DEBUG = False

ALLOWED_HOSTS = ["*"]

LOGIN_REDIRECT_URL = '/numbers'
MAX_USERNAME_LENGTH = 255

LOGIN_URL = reverse_lazy('login')

AUTH_USER_MODEL = "apps.User"

# Email

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.sendgrid.com"
EMAIL_PORT = "587"
EMAIL_HOST_USER = "mybusinessbenchmark-mailman"
EMAIL_HOST_PASSWORD = "5=RdyHQ#R'2tB9W}"

DEFAULT_EMAIL_FROM = "MyBusinessBenchmark.com.au <no-reply@mybusinessbenchmark.com.au>"
DEFAULT_SITE_NAME = "MyBusinessBenchmark.com.au"
DEFAULT_DOMAIN_NAME = "mybusinessbenchmark.com.au"

CONTACTS_EMAIL_SEND_TO = ["nikki@stefankazakis.com", "tkudla@ettera.com"]

# Application definition

RE_CAPTCHA_SECRET = "6LcgbhsTAAAAALSdlzSX7ETXcvBxgJneDTPPsnQs"
RE_CAPTCHA_SITE_KEY = "6LcgbhsTAAAAAPM-__n1yoAafbp4Bg02cztHWIqw"
RE_CAPTCHA_ENABLED = True

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    'password_reset',
    'impersonate',
    'widget_tweaks',
    'apps',
    'django.contrib.admin',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.exception.ExceptionLoggingMiddleware',
    'middleware.user_active.UserActiveMiddleware',
    # Impersonation
    'impersonate.middleware.ImpersonateMiddleware',
)

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'templates')],
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


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Melbourne'
USE_I18N = True
USE_L10N = True
USE_TZ = True

IMPERSONATE_CUSTOM_ALLOW = "apps.groups.views.is_allowed_impersonate"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, "static"),
)

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

COMPRESS_ROOT = os.path.join(PROJECT_DIR, "static")

COMPRESS_CSS_FILTERS = [
     'compressor.filters.cssmin.CSSMinFilter',
]

COMPRESS_ENABLED = True

try:
    from local_config import *
except ImportError:
    print("Can't find local settings")
