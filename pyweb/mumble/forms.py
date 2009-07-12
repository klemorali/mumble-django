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

from django			import forms
from django.forms	import Form, ModelForm
from models		import *

class MumbleForm( ModelForm ):
	"""
	The Mumble Server admin form that allows to configure settings which do not necessarily
	have to be reserved to the server hoster.
	
	Server hosters are expected to use the Django admin application instead, where everything
	can be configured freely.
	"""
	class Meta:
		model   = Mumble;
		exclude = ( 'dbus', 'booted', 'addr', 'port', 'users', 'bwidth', 'sslcrt', 'sslkey', );
	

class MumbleUserForm( ModelForm ):
	"""The user registration form used to register an account."""
	class Meta:
		model   = MumbleUser;
		fields  = ( 'name', 'password' );


class MumbleTextureForm( Form ):
	"""The form used to upload a new image to be set as texture."""
	texturefile = forms.ImageField();


