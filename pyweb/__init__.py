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

from django.core import signals

def update_paths( **kwargs ):
	from django.core.urlresolvers import get_script_prefix, reverse
	from os.path     import join
	from django.conf import settings
	pf = get_script_prefix();
	settings.MEDIA_URL          = "%sstatic" % pf;
	settings.ADMIN_MEDIA_PREFIX = "%smedia"  % pf;
	settings.LOGIN_URL          = reverse( "django.contrib.auth.views.login" );
	signals.request_started.disconnect( update_paths );

signals.request_started.connect( update_paths );
