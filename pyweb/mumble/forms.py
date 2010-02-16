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

import socket
import re

from django			import forms
from django.conf		import settings
from django.forms		import Form, ModelForm
from django.utils.translation	import ugettext_lazy as _

from mumble.models		import Mumble, MumbleUser


class PropertyModelForm( ModelForm ):
	""" ModelForm that gets/sets fields that are not within the model's
	    fields as model attributes. Necessary to get forms that manipulate
	    properties.
	"""
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs );
		
		instfields = self.instance._meta.get_all_field_names()
		
		for fldname in self.fields:
			if fldname not in instfields:
				self.fields[fldname].initial = getattr( self.instance, fldname )
	
	def save( self, commit=True ):
		inst = ModelForm.save( self, commit=commit )
		
		instfields = inst._meta.get_all_field_names()
		
		for fldname in self.fields:
			if fldname not in instfields:
				setattr( inst, fldname, self.cleaned_data[fldname] )
		
		return inst


def populate_channel_choices( form ):
	""" Populate the `default channel' field's choices """
	choices = [ ('', '----------') ]
	
	def add_item( item, level ):
		if item.is_server or item.is_channel:
			choices.append( ( str(item.chanid), ( "-"*level + " " + item.name ) ) )
	
	form.instance.rootchan.visit(add_item)
	
	form.fields['defchan'].choices = choices


class MumbleAdminForm( ModelForm ):
	""" A Mumble Server admin form intended to be used by the server hoster. """
	defchan = forms.TypedChoiceField( choices=(), coerce=int )
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs )
		populate_channel_choices( self )
	
	class Meta:
		model   = Mumble;
	
	def clean_port( self ):
		""" If portno == -1 autoassign, and check if the port number is valid. """
		
		port = self.cleaned_data['port'];
		if port == -1:
			port = max( [ rec['port'] for rec in Mumble.objects.values('port') ] ) + 1;
		
		if port < 1 or port >= 2**16:
			raise forms.ValidationError(
				_("Port number %(portno)d is not within the allowed range %(minrange)d - %(maxrange)d") % {
				'portno':   port,
				'minrange': 1,
				'maxrange': 2**16,
				});
		return port;
	
	def clean( self ):
		""" Try to bind to the addr and port to verify that they are available. """
		
		if self.instance.id is not None or 'addr' not in self.cleaned_data or 'port' not in self.cleaned_data:
			# Editing old instance or previous validation failed already, don't try to bind
			return self.cleaned_data;
		
		addr = socket.gethostbyname( self.cleaned_data['addr'] );
		port = self.cleaned_data['port'];
		
		try:
			socktcp = socket.socket( socket.AF_INET, socket.SOCK_STREAM );
			socktcp.bind( ( addr, port ) );
		except socket.error, err:
			raise forms.ValidationError( err.args[1] );
		finally:
			socktcp.close();
		
		try:
			sockudp = socket.socket( socket.AF_INET, socket.SOCK_DGRAM  );
			sockudp.bind( ( addr, port ) );
		except socket.error, err:
			raise forms.ValidationError( err.args[1] );
		finally:
			sockudp.close();
		
		return self.cleaned_data;


class MumbleForm( ModelForm ):
	"""
	The Mumble Server admin form that allows to configure settings which do not necessarily
	have to be reserved to the server hoster.
	
	Server hosters are expected to use the Django admin application instead, where everything
	can be configured freely.
	"""
	
	defchan = forms.TypedChoiceField( choices=(), coerce=int )
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs )
		populate_channel_choices( self )
	
	class Meta:
		model   = Mumble;
		exclude = ( 'dbus', 'booted', 'addr', 'port', 'users', 'bwidth', 'sslcrt', 'sslkey', );


class MumbleUserForm( ModelForm ):
	""" The user registration form used to register an account. """
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs );
		self.server = None;
	
	def clean_name( self ):
		""" Check if the desired name is forbidden or taken. """
		
		name = self.cleaned_data['name'];
		
		if self.server is None:
			raise AttributeError( "You need to set the form's server attribute to the server instance "
				"for validation to work." );
		
		if self.server.player and re.compile( self.server.player ).match( name ) is None:
			raise forms.ValidationError( _( "That name is forbidden by the server." ) );
		
		if not self.instance.id and len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) > 0:
			raise forms.ValidationError( _( "Another player already registered that name." ) );
		
		return name;
	
	def clean_password( self ):
		""" Verify a password has been given. """
		passwd = self.cleaned_data['password'];
		if not passwd:
			raise forms.ValidationError( _( "Cannot register player without a password!" ) );
		return passwd;
	
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
		""" Validate the password """
		serverpw = self.cleaned_data['serverpw'];
		if self.server.passwd != serverpw:
			raise forms.ValidationError( _( "The password you entered is incorrect." ) );
		return serverpw;
	
	def clean( self ):
		""" prevent save() from trying to store the password in the Model instance. """
		# clean() will be called after clean_serverpw(), so it has already been validated here.
		if 'serverpw' in self.cleaned_data:
			del( self.cleaned_data['serverpw'] );
		return self.cleaned_data;


class MumbleUserLinkForm( MumbleUserForm ):
	""" Special registration form to either register or link an account. """
	
	linkacc = forms.BooleanField(
		label=_('Link account'),
		help_text=_('The account already exists and belongs to me, just link it instead of creating.'),
		required=False,
		);	
	
	def __init__( self, *args, **kwargs ):
		MumbleUserForm.__init__( self, *args, **kwargs );
		self.mumbleid = None;
	
	def clean_name( self ):
		""" Check if the target account exists in Murmur. """
		if 'linkacc' not in self.data:
			return MumbleUserForm.clean_name( self );
		
		# Check if user exists
		name = self.cleaned_data['name'];
		
		if len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) != 1:
			raise forms.ValidationError( _( "No such user found." ) );
		
		return name;
	
	def clean_password( self ):
		""" Verify that the password is correct. """
		if 'linkacc' not in self.data:
			return MumbleUserForm.clean_password( self );
		
		if 'name' not in self.cleaned_data:
			# keep clean() from trying to find a user that CAN'T exist
			self.mumbleid = -10;
			return '';
		
		# Validate password with Murmur
		passwd = self.cleaned_data['password'];
		
		self.mumbleid = self.server.ctl.verifyPassword( self.server.srvid, self.cleaned_data['name'], passwd )
		if self.mumbleid <= 0:
			raise forms.ValidationError( _( "The password you entered is incorrect." ) );
		
		return passwd;
	
	def clean( self ):
		""" Create the MumbleUser instance to save in. """
		if 'linkacc' not in self.data or self.mumbleid <= 0:
			return self.cleaned_data;
		
		try:
			m_user = MumbleUser.objects.get( server=self.server, mumbleid=self.mumbleid );
		except MumbleUser.DoesNotExist:
			m_user = MumbleUser( server=self.server, name=self.cleaned_data['name'], mumbleid=self.mumbleid );
			m_user.isAdmin = m_user.getAdmin();
			m_user.save( dontConfigureMurmur=True );
		else:
			if m_user.owner is not None:
				raise forms.ValidationError( _( "That account belongs to someone else." ) );
		
		if m_user.getAdmin() and not settings.ALLOW_ACCOUNT_LINKING_ADMINS:
			raise forms.ValidationError( _( "Linking Admin accounts is not allowed." ) );
		self.instance = m_user;
		
		return self.cleaned_data;


class MumbleUserAdminForm( PropertyModelForm ):
	aclAdmin = forms.BooleanField( label=_('Admin on root channel'), required=False );
	
	class Meta:
		model   = Mumble;


class MumbleTextureForm( Form ):
	""" The form used to upload a new image to be set as texture. """
	texturefile = forms.ImageField();


