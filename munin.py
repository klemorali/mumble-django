#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

# This is PerlDoc documentation (POD) to be viewed with munindoc (or perldoc).

"""
=head1 NAME

mumble-django - graph Mumble user counts for server instances

=head1 DESCRIPTION

This plugin monitors the number of users connected to the Mumble server
instances configured in Mumble-Django. It automatically adapts to servers
being offline, new servers being added and servers being deleted, and
therefore should not require too much maintenance.

=head1 APPLICABLE SYSTEMS

Mumble servers that have Mumble-Django installed.

=head1 SYNOPSIS

B<munin-run mumble-django> [config|autoconf]

=head1 OPTIONS

=over 4

=item B<config>   - emit graph configuration options for Munin to use.

=item B<autoconf> - check if the plugin can be safely installed.

=back

If neither are given, the plugin will emit the current user counts for each
known server instance.

=head1 CONFIGURATION

The plugin is configured in the I<settings.py> file along with your
Mumble-Django installation. The plugin allows self-testing to see if it has
everything it needs in order to run; just run it with the parameter "autoconf"
and the plugin will tell you if it can be safely installed.

The following variables are relevant in I<settings.py>:

=over 4

=item B<MUNIN_WARNING>  - the "warning" level factor, defaults to 0.80.

=item B<MUNIN_CRITICAL> - the "critical" level factor, defaults to 0.95.

=item B<MUNIN_TITLE>    - the title of the graph, defaults to "Mumble Users".

=item B<MUNIN_CATEGORY> - the category the graphs appear in, defaults to "network".

=back

All of these settings can be overridden in I<settings.py> simply by defining
them there. If a variable is omitted, the defaults are used as specified.

The WARNING and CRITICAL level factors are multiplied with the server's slot
count to form the real thresholds.

=head1 MAGIC MARKERS

  #%# family=auto
  #%# capabilities=autoconf

=head1 BUGS

Bugs are tracked along with Mumble-Django bugs in the issue tracker:

	http://bitbucket.org/Svedrin/mumble-django/issue/

If you find a bug, please report it.

=head1 AUTHOR

Copyright (C) 2009 - 2010, Michael "Svedrin" Ziegler

=head1 LICENSE

Mumble-Django is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

=cut
"""

# Set this to the same path you used in settings.py, or None for auto-detection.
MUMBLE_DJANGO_ROOT = None

### DO NOT CHANGE ANYTHING BELOW THIS LINE ###

import os, sys
from os.path import join, dirname, abspath, exists

# Path auto-detection
if not MUMBLE_DJANGO_ROOT or not exists( MUMBLE_DJANGO_ROOT ):
    MUMBLE_DJANGO_ROOT = dirname(abspath(__file__))

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
        print "srv%d.label %s" % ( mumble.id, mumble.name.replace('#', '').encode(prefenc, "replace") )
        if mumble.connecturl:
            print "srv%d.info %s"  % ( mumble.id, mumble.connecturl )
        if mumble.users:
            print "srv%d.warning %d"  % ( mumble.id, int( mumble.users * warn ) )
            print "srv%d.critical %d" % ( mumble.id, int( mumble.users * crit ) )


elif sys.argv[-1] == 'autoconf':
    if Mumble.objects.count() == 0:
        print "no (no servers configured)"
    else:
        # check if connecting works
        try:
            for mumble in get_running_instances():
                mumble.ctl
        except Exception, instance:
            print "no (can't connect to server %s: %s)" % ( mumble.name, instance )
        else:
            print "yes"


else:
    for mumble in get_running_instances():
        print "srv%d.value %d" % ( mumble.id, len( mumble.ctl.getPlayers( mumble.srvid ) ) )

