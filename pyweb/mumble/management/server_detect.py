# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright © 2009-2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

import os, getpass

from django.db      import DatabaseError
from django.conf    import settings

from mumble.models  import MumbleServer, Mumble, signals
from mumble.mctl    import MumbleCtlBase


def find_in_dicts( keys, conf, default, valueIfNotFound=None ):
    if not isinstance( keys, tuple ):
        keys = ( keys, )

    for keyword in keys:
        if keyword in conf:
            return conf[keyword]

    for keyword in keys:
        keyword = keyword.lower()
        if keyword in default:
            return default[keyword]

    return valueIfNotFound


def find_existing_instances( **kwargs ):
    if "verbosity" in kwargs:
        v = kwargs['verbosity']
    else:
        v = 1

    if v > 1:
        print "Starting Mumble servers and players detection now."

    triedEnviron = False
    online = False
    while not online:
        env_icesecret = None
        if not triedEnviron and 'MURMUR_CONNSTR' in os.environ:
            dbusName = os.environ['MURMUR_CONNSTR']
            if 'MURMUR_ICESECRET' in os.environ:
                env_icesecret = os.environ['MURMUR_ICESECRET']
            triedEnviron = True
            if v > 1:
                print "Trying environment setting", dbusName
        else:
            print "--- Murmur connection info ---"
            print "  1) DBus -- net.sourceforge.mumble.murmur  (Murmur 1.1.8 or older)"
            print "  2) ICE  -- Meta:tcp -h 127.0.0.1 -p 6502  (Recommended)"
            print
            print "Enter 1 or 2 for the defaults above, nothing to skip Server detection,"
            print "and if the defaults do not fit your needs, enter the correct string."
            print "Whether to use DBus or Ice will be detected automatically from the"
            print "string's format."
            print

            dbusName = raw_input( "Service string: " ).strip()

        if not dbusName:
            if v:
                print 'Be sure to run "python manage.py syncdb" with Murmur running before'
                print "trying to use this app! Otherwise, existing Murmur servers won't be"
                print 'configurable!'
            return False
        elif dbusName == "1":
            dbusName = "net.sourceforge.mumble.murmur"
        elif dbusName == "2":
            dbusName = "Meta:tcp -h 127.0.0.1 -p 6502"

        if env_icesecret is None:
            icesecret = getpass.getpass("Please enter the Ice secret (if any): ")
        else:
            icesecret = env_icesecret

        try:
            ctl = MumbleCtlBase.newInstance( dbusName, settings.SLICE, icesecret )
        except Exception, instance:
            if v:
                print "Unable to connect using name %s. The error was:" % dbusName
                print instance
                print
        else:
            online = True
            if v > 1:
                print "Successfully connected to Murmur via connection string %s, using %s." % ( dbusName, ctl.method )

    try:
        meta = MumbleServer.objects.get( dbus=dbusName )
    except MumbleServer.DoesNotExist:
        meta = MumbleServer( dbus=dbusName )
    finally:
        meta.secret = icesecret
        meta.save(run_detection=True, verbosity=v)

    print "Successfully finished Servers and Players detection."
    print "To add more servers, run this command again."
    return True


