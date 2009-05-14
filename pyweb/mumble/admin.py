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

from models import *
from django.contrib import admin

class MumbleAdmin(admin.ModelAdmin):
	list_display   = [ 'name', 'addr', 'port', 'booted' ];
	list_filter    = [ 'booted' ];
	search_fields  = [ 'name', 'addr' ];
	ordering       = [ 'name' ];

class MumbleUserAdmin(admin.ModelAdmin):
	list_display   = [ 'owner', 'server', 'name' ];
	list_filter    = [ 'server' ];
	search_fields  = [ 'owner__username', 'name' ];
	ordering       = [ 'owner__username' ];


admin.site.register( Mumble, MumbleAdmin );
admin.site.register( MumbleUser, MumbleUserAdmin );
