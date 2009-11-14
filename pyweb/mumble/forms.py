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

import re

from django			import forms
from django.forms		import Form, ModelForm
from django.utils.translation	import ugettext_lazy as _

from models			import *


class MumbleAdminForm( ModelForm ):
	""" A Mumble Server admin form intended to be used by the server hoster. """
	class Meta:
		model   = Mumble;
		exclude = ( 'sslcrt', 'sslkey' );


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
	""" The user registration form used to register an account. """
	
	def clean_name( self ):
		name = self.cleaned_data['name'];
		
		if self.server.player and re.compile( self.server.player ).match( name ) is None:
			raise forms.ValidationError( _( "That name is forbidden by the server." ) );
		
		if not self.instance.id and len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) > 0:
			raise forms.ValidationError( _( "Another player already registered that name." ) );
		
		return name;
	
	def clean_password( self ):
		pw = self.cleaned_data['password'];
		if not pw:
			raise forms.ValidationError( _( "Cannot register player without a password!" ) );
		return pw;
	
	class Meta:
		model   = MumbleUser;
		fields  = ( 'name', 'password' );


class MumbleUserPasswordForm( MumbleUserForm ):
	""" The user registration form used to register an account on a private server in protected mode. """
	
	serverpw = forms.CharField(
		label=_('Server Password'),
		help_text=_('This server is private and protected mode is active. Please enter the server password.'),
		widget=forms.PasswordInput(render_value=False)
		);
	
	def clean_serverpw( self ):
		# Validate the password
		serverpw = self.cleaned_data['serverpw'];
		if self.server.passwd != serverpw:
			raise forms.ValidationError( _( "The password you entered is incorrect." ) );
		return serverpw;
	
	def clean( self ):
		# prevent save() from trying to store the password in the Model instance
		# clean() will be called after clean_serverpw(), so it has already been validated here.
		if 'serverpw' in self.cleaned_data:
			del( self.cleaned_data['serverpw'] );
		return self.cleaned_data;


class MumbleUserLinkForm( MumbleUserForm ):
	""" Special registration form to either register or link an account. """
	
	linkacc = forms.BooleanField(
		label=_('Link account'),
		help_text=_('The account already exists and belongs to me, just link it instead of creating.'),
		);	
	
	def clean_name( self ):
		if 'linkacc' not in self.data:
			return MumbleUserForm.clean_name( self );
		
		# Check if user exists
		name = self.cleaned_data['name'];
		
		if len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) != 1:
			raise forms.ValidationError( _( "No such user found." ) );
		
		return name;
	
	def clean_password( self ):
		if 'linkacc' not in self.data:
			return MumbleUserForm.clean_password( self );
		
		# Validate password with Murmur
		pw = self.cleaned_data['password'];
		
		self.mumbleid = self.server.ctl.verifyPassword( self.server.srvid, self.cleaned_data['name'], pw )
		if self.mumbleid <= 0:
			raise forms.ValidationError( _( "The password you entered is incorrect." ) );
		
		return pw;
	
	def clean( self ):
		if 'linkacc' not in self.data:
			return self.cleaned_data;
		
		mUser = MumbleUser.objects.get( server=self.server, mumbleid=self.mumbleid );
		if mUser.getAdmin() and not settings.ALLOW_ACCOUNT_LINKING_ADMINS:
			raise forms.ValidationError( "Linking Admin accounts is not allowed." );
		self.instance = mUser;
		
		return self.cleaned_data;
	
	def save( self, *args, **kwargs ):
		inst = MumbleUserForm.save( self, *args, **kwargs );
		
		if 'linkacc' not in self.data:
			inst.isAdmin = False;
			inst.server  = this.server;
		
		return inst;


class MumbleTextureForm( Form ):
	""" The form used to upload a new image to be set as texture. """
	texturefile = forms.ImageField();


