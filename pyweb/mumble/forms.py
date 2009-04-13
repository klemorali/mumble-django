# -*- coding: utf-8 -*-
from django.forms	import ModelForm
from models		import *

class MumbleForm( ModelForm ):
	class Meta:
		model   = Mumble;
		exclude = ( 'dbus', 'booted', 'addr', 'port', 'users', 'bwidth', 'sslcrt', 'sslkey', );
	

class MumbleUserForm( ModelForm ):
	class Meta:
		model   = MumbleUser;
		fields  = ( 'name', 'password' );

