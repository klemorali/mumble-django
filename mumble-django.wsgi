import os, sys

# Set this to the same path you used in settings.py.
MUMBLE_DJANGO_ROOT = '/home/mistagee/mumble-django/hgrep';


sys.path.append( MUMBLE_DJANGO_ROOT )
sys.path.append( MUMBLE_DJANGO_ROOT+'/pyweb' )
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyweb.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

