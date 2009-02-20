import os, sys

sys.path.append( '/usr/share/mumble-django' )
sys.path.append( '/usr/share/mumble-django/pyweb' )
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyweb.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

