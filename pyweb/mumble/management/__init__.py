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

from django.db		import connection, transaction
from django.db.models	import signals

from mumble		import models

from update_schema	import update_schema
from server_detect	import find_existing_instances


if not transaction.is_managed():
	managed_before = False
	transaction.enter_transaction_management(True)
	transaction.managed(True)
else:
	managed_before = True


cursor = connection.cursor()
try:
	cursor.execute( "SELECT server_id FROM mumble_mumble;" )

except cursor.db.connection.Error:
	# server_id field does not exist -> DB needs to be updated.
	transaction.rollback()
	signals.post_syncdb.connect( update_schema, sender=models );

else:
	transaction.rollback()
	signals.post_syncdb.connect( find_existing_instances, sender=models );

finally:
	if not managed_before:
		transaction.managed(False)
		transaction.leave_transaction_management()


