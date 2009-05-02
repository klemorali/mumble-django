#!/bin/bash
#
#  Copyright (C) 2009, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
#
#  Mumble-Django is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This package is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# I know this script sucks ass, thank you very much - but it should do the
# trick. It creates the columns in the database that have been added in v0.6.
#

<<EOF ./manage.py shell >/dev/null
# -*- coding: utf-8 -*-
from django.db   import connection
from django.conf import settings
crs = connection.cursor();

crs.execute( "ALTER TABLE mumble_mumble ADD obfsc   BOOLEAN      NOT NULL DEFAULT 0"   );
crs.execute( "ALTER TABLE mumble_mumble ADD player  VARCHAR(200) NOT NULL DEFAULT '%s'" % r'[-=\\w\\[\\]\\{\\}\\(\\)\\@\\|\\.]+'    );
crs.execute( "ALTER TABLE mumble_mumble ADD channel VARCHAR(200) NOT NULL DEFAULT '%s'" % r'[ \\-=\\w\\#\\[\\]\\{\\}\\(\\)\\@\\|]+' );
crs.execute( "ALTER TABLE mumble_mumble ADD defchan INTEGER      NOT NULL DEFAULT 0"   );
EOF
