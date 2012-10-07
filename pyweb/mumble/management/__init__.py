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

from shutil           import copy, move
from os.path          import exists, join

from django.conf      import settings
from django.db        import connection
from django.db.models import signals

from mumble           import models

from update_schema    import update_schema
from server_detect    import find_existing_instances


if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    # Move the DB to the db subdirectory if necessary.
    oldpath = join( settings.MUMBLE_DJANGO_ROOT, "mumble-django.db3" )
    if not exists( settings.DATABASES["default"]["NAME"] ) and exists( oldpath ):
        move( oldpath, settings.DATABASES["default"]["NAME"] )


cursor = connection.cursor()

tablename = models.Mumble._meta.db_table

if tablename in connection.introspection.get_table_list(cursor):
    fields = connection.introspection.get_table_description(cursor, tablename)
    uptodate = "server_id" in [ entry[0] for entry in fields ]
else:
    # Table doesn't yet exist, so syncdb will create it properly
    uptodate = True

if not uptodate:
    if settings.DATABASE["default"]["ENGINE"] == "django.db.backends.sqlite3":
        # backup the db before the conversion.
        copy( settings.DATABASES["default"]["NAME"], settings.DATABASES["default"]["NAME"]+".bak" )
    signals.post_syncdb.connect( update_schema, sender=models )
else:
    signals.post_syncdb.connect( find_existing_instances, sender=models )


