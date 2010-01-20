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

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from forms  import MumbleAdminForm
from models import Mumble, MumbleUser

class MumbleAdmin(admin.ModelAdmin):
	list_display   = [ 'name', 'addr', 'port', 'booted', 'getIsPublic', 'getUsersRegged', 'getUsersOnline', 'getChannelCnt' ];
	list_filter    = [ 'booted', 'addr' ];
	search_fields  = [ 'name', 'addr' ];
	ordering       = [ 'name' ];
	form           = MumbleAdminForm;
	
	def getUsersRegged( self, obj ):
		return obj.users_regged;
	getUsersRegged.short_description = _( 'Registered users' );
	
	def getUsersOnline( self, obj ):
		return obj.users_online;
	getUsersOnline.short_description = _( 'Online users' );
	
	def getChannelCnt( self, obj ):
		return obj.channel_cnt;
	getChannelCnt.short_description = _( 'Channel count' );
	
	def getIsPublic( self, obj ):
		if obj.is_public:
			return _( 'Yes' );
		return _( 'No' );
	getIsPublic.short_description = _( 'Public' );
	

class MumbleUserAdmin(admin.ModelAdmin):
	list_display   = [ 'owner', 'server', 'name', 'isAdmin' ];
	list_filter    = [ 'server' ];
	search_fields  = [ 'owner__username', 'name' ];
	ordering       = [ 'owner__username' ];


admin.site.register( Mumble, MumbleAdmin );
admin.site.register( MumbleUser, MumbleUserAdmin );
