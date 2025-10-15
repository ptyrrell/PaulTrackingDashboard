"""
WSGI config for knr project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os

# Use production settings on Heroku, local settings otherwise
if 'DYNO' in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
