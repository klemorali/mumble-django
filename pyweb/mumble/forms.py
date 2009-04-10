from django.forms	import ModelForm
from models			import *

class MumbleForm( ModelForm ):
	class Meta:
		model   = Mumble;
		exclude = ( 'dbus', 'booted', 'addr', 'port', 'users', 'bwidth', );
	

