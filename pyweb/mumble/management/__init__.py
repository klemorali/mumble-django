# -*- coding: utf-8 -*-

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

from django.db		import connection
from django.db.models	import signals

from mumble		import models

from update_schema	import update_schema
from server_detect	import find_existing_instances

cursor = connection.cursor()

tablename = models.Mumble._meta.db_table

uptodate  = False
if tablename in connection.introspection.get_table_list(cursor):
	fields = connection.introspection.get_table_description(cursor, tablename)
	for entry in fields:
		if entry[0] == "server_id":
			uptodate = True
			break
else:
	# Table doesn't yet exist, so syncdb will create it properly
	uptodate = True

if not uptodate:
	signals.post_syncdb.connect( update_schema, sender=models );
else:
	signals.post_syncdb.connect( find_existing_instances, sender=models );


