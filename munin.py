#!/usr/bin/python

# Set this to the same path you used in settings.py, or None for auto-detection.
MUMBLE_DJANGO_ROOT = None;

### DO NOT CHANGE ANYTHING BELOW THIS LINE ###

import os, sys
from os.path import join, dirname, abspath, exists

# Path auto-detection
if not MUMBLE_DJANGO_ROOT or not exists( MUMBLE_DJANGO_ROOT ):
	MUMBLE_DJANGO_ROOT = dirname(abspath(__file__));

# environment variables
sys.path.append( MUMBLE_DJANGO_ROOT )
sys.path.append( join( MUMBLE_DJANGO_ROOT, 'pyweb' ) )
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyweb.settings'


# If you get an error about Python not being able to write to the Python
# egg cache, the egg cache path might be set awkwardly. This should not
# happen under normal circumstances, but every now and then, it does.
# Uncomment this line to point the egg cache to /tmp.
#os.environ['PYTHON_EGG_CACHE'] = '/tmp/pyeggs'

from mumble.models import *
mm = Mumble.objects.filter( booted = True )

if sys.argv[-1] == 'config':
	print "graph_vlabel Users"
	print "graph_args --base 1000"
	print "graph_title Mumble Users"
	print "graph_category network"
	
	for mumble in mm:
		print "%d.label %s" % ( mumble.id, mumble.name );

else:
	for mumble in mm:
		print "%d.value %d" % ( mumble.id, len( mumble.ctl.getPlayers( mumble.srvid ) ) );

