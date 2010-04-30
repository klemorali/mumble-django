#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 *  Copyright (C) 2009, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *
 *  Mumble-Django is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

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

import locale
from django.conf   import settings
from mumble.models import MumbleServer, Mumble

warn  = getattr( settings, "MUNIN_WARNING",  0.80 )
crit  = getattr( settings, "MUNIN_CRITICAL", 0.95 )
title = getattr( settings, "MUNIN_TITLE",    "Mumble Users" )
categ = getattr( settings, "MUNIN_CATEGORY", "network"      )


def get_running_instances():
	for server in MumbleServer.objects.all():
		if not server.online:
			continue
		runinst = server.ctl.getBootedServers()
		for inst in server.mumble_set.order_by("srvid").filter( srvid__in=runinst ):
			yield inst


if sys.argv[-1] == 'config':
	prefenc = locale.getpreferredencoding()
	
	print "graph_vlabel Users"
	print "graph_args --base 1000"
	print "graph_title", title
	print "graph_category", categ
	
	for mumble in get_running_instances():
		print "srv%d.label %s" % ( mumble.id, mumble.name.replace('#', '').encode(prefenc, "replace") );
		if mumble.connecturl:
			print "srv%d.info %s"  % ( mumble.id, mumble.connecturl );
		if mumble.users:
			print "srv%d.warning %d"  % ( mumble.id, int( mumble.users * warn ) );
			print "srv%d.critical %d" % ( mumble.id, int( mumble.users * crit ) );


elif sys.argv[-1] == 'autoconf':
	if Mumble.objects.count() == 0:
		print "no (no servers configured)";
	else:
		# check if connecting works
		try:
			for mumble in get_running_instances():
				mumble.ctl
		except Exception, instance:
			print "no (can't connect to server %s: %s)" % ( mumble.name, instance );
		else:
			print "yes";


else:
	for mumble in get_running_instances():
		print "srv%d.value %d" % ( mumble.id, len( mumble.ctl.getPlayers( mumble.srvid ) ) );

