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

from django                 import template
from django.template.loader import render_to_string

from django.conf            import settings

register = template.Library();



### FILTER: trunc -- converts "a very very extaordinary long text" to "a very very extra..."
def trunc( string, maxlen = 50 ):
	if len(string) < maxlen:
		return string;
	return string[:(maxlen - 3)] + "...";

register.filter( 'trunc', trunc );


### FILTER: chanview -- renders an mmChannel / mmPlayer object with the correct template.
def chanview( obj, user = None ):
	if obj.is_server:
		return render_to_string( 'mumble/server.htm',  { 'Server':  obj, 'MumbleAccount': user, 'MEDIA_URL': settings.MEDIA_URL } );
	elif obj.is_channel:
		return render_to_string( 'mumble/channel.htm', { 'Channel': obj, 'MumbleAccount': user, 'MEDIA_URL': settings.MEDIA_URL } );
	elif obj.is_player:
		return render_to_string( 'mumble/player.htm',  { 'Player':  obj, 'MumbleAccount': user, 'MEDIA_URL': settings.MEDIA_URL } );

register.filter( 'chanview', chanview );


### FILTER: chanurl -- creates a connection URL and takes the user's login into account
def chanurl( obj, user ):
	return obj.getURL( user );

register.filter( 'chanurl', chanurl );


