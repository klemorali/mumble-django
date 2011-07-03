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

import os
from os.path import dirname

from django.core.management.base import BaseCommand
from django.contrib.auth.models  import User
from django.contrib.sites.models import Site
from django.conf                 import settings

from mumble.models import Mumble, MumbleServer


class TestFailed( Exception ):
    pass

class Command( BaseCommand ):
    help = "Run a few tests on Mumble-Django's setup."

    def handle(self, **options):
        try:
            import Ice
        except ImportError:
            pass
        else:
            self.check_slice()

        self.check_rootdir()
        self.check_dbase()
        self.check_sites()
        self.check_mumbles()
        self.check_admins()
        self.check_secret_key()

    def check_slice( self ):
        print "Checking slice file for %d server instances..." % MumbleServer.objects.count(),
        for serv in MumbleServer.objects.all():
            if serv.method_ice:
                serv.ctl

        print "[ OK ]"

    def check_rootdir( self ):
        print "Checking root directory access...",
        if not os.path.exists( settings.MUMBLE_DJANGO_ROOT ):
            raise TestFailed( "The mumble-django root directory does not exist." )

        elif "sqlite3" not in settings.DATABASES["default"]["ENGINE"]:
            print "not using sqlite [ OK ]"

        else:
            for checkdir in ( settings.MUMBLE_DJANGO_ROOT, dirname(settings.DATABASES["default"]["NAME"]) ):
                statinfo = os.stat( checkdir )

                if statinfo.st_uid == 0:
                    raise TestFailed(
                        "The directory '%s' belongs to user root. This is "
                        "most certainly not what you want because it will prevent your "
                        "web server from being able to write to the database. Please check." % checkdir )

                elif not os.access( checkdir, os.W_OK ):
                    raise TestFailed( "The directory '%s' is not writable." % checkdir )

            print "[ OK ]"

    def check_dbase( self ):
        print "Checking database access...",
        if "sqlite3" in settings.DATABASES["default"]["ENGINE"]:
            if not os.path.exists( settings.DATABASES["default"]["NAME"] ):
                raise TestFailed( "database does not exist. Have you run syncdb yet?" )

            else:
                statinfo = os.stat( settings.DATABASES["default"]["NAME"] )

                if statinfo.st_uid == 0:
                    raise TestFailed(
                        "the database file belongs to root. This is most certainly not what "
                        "you want because it will prevent your web server from being able "
                        "to write to it. Please check." )

                elif not os.access( settings.DATABASES["default"]["NAME"], os.W_OK ):
                    raise TestFailed( "database file is not writable." )

                else:
                    print "[ OK ]"

        else:
            print "not using sqlite, so I can't check."


    def check_sites( self ):
        print "Checking URL configuration...",

        try:
            site = Site.objects.get_current()

        except Site.DoesNotExist:
            try:
                sid = settings.SITE_ID
            except AttributeError:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(
                    "You're using the Django \"sites framework\" without having set the SITE_ID "
                    "setting. Create a site in your database and rerun this command to fix this error.")
            else:
                print(  "none set.\n"
                    "Please enter the domain where Mumble-Django is reachable." )
                dom = raw_input( "> " ).strip()
                site = Site( id=sid, name=dom, domain=dom )
                site.save()

        if site.domain == 'example.com':
            print(  "still the default.\n"
                "The domain is configured as example.com, which is the default but does not make sense. "
                "Please enter the domain where Mumble-Django is reachable." )

            site.domain = raw_input( "> " ).strip()
            site.save()

        print site.domain, "[ OK ]"


    def check_admins( self ):
        print "Checking if an Admin user exists...",

        for user in User.objects.all():
            if user.is_superuser:
                print "[ OK ]"
                return

        raise TestFailed( ""
            "No admin user exists, so you won't be able to log in to the admin system. You "
            "should run `./manage.py createsuperuser` to create one." )


    def check_mumbles( self ):
        print "Checking Murmur instances...",

        mm = Mumble.objects.all()

        if mm.count() == 0:
            raise TestFailed(
                "no Mumble servers are configured, you might want to run "
                "`./manage.py syncdb` to run an auto detection." )

        else:
            for mumble in mm:
                try:
                    mumble.ctl
                except Exception, err:
                    raise TestFailed(
                        "Connecting to Murmur `%s` (%s) failed: %s" % ( mumble.name, mumble.server, err )
                        )
            print "[ OK ]"

    def check_secret_key( self ):
        print "Checking SECRET_KEY...",

        blacklist = ( 'u-mp185msk#z4%s(do2^5405)y5d!9adbn92)apu_p^qvqh10v', )

        if settings.SECRET_KEY in blacklist:
            raise TestFailed(
                "Your SECRET_KEY setting matches one of the keys that were put in the settings.py "
                "file shipped with Mumble-Django, which means your SECRET_KEY is all but secret. "
                "You should change the setting, or remove it altogether and allow the key to be "
                "generated automatically."
                )
        else:
            print "[ OK ]"






