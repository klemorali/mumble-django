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

from PIL    import Image
from struct import pack, unpack
from zlib   import compress, decompress

from django.contrib.auth.models import User
from django.db import models

from mmobjects import mmServer, mmACL

from django.conf import settings

from mctl import *

import socket

class Mumble( models.Model ):
	name   = models.CharField(    'Server Name',        max_length = 200 );
	dbus   = models.CharField(    'DBus base',          max_length = 200, default = 'net.sourceforge.mumble.murmur' );
	srvid  = models.IntegerField( 'Server ID',          editable = False );
	addr   = models.CharField(    'Server Address',     max_length = 200 );
	port   = models.IntegerField( 'Server Port',                          blank = True, null = True  );
	url    = models.CharField(    'Website URL',        max_length = 200, blank = True );
	motd   = models.TextField(    'Welcome Message',                      blank = True );
	passwd = models.CharField(    'Server Password',    max_length = 200, blank = True );
	supw   = models.CharField(    'Superuser Password', max_length = 200, blank = True );
	users  = models.IntegerField( 'Max. Users',                           blank = True, null = True );
	bwidth = models.IntegerField( 'Bandwidth [Bps]',                      blank = True, null = True );
	sslcrt = models.TextField(    'SSL Certificate',                      blank = True   );
	sslkey = models.TextField(    'SSL Key',            blank = True   );
	obfsc  = models.BooleanField( 'IP Obfuscation',     default = False );
	player = models.CharField(    'Player name regex',  max_length=200, default=r'[-=\w\[\]\{\}\(\)\@\|\.]+' );
	channel= models.CharField(    'Channel name regex', max_length=200, default=r'[ \-=\w\#\[\]\{\}\(\)\@\|]+' );
	defchan= models.IntegerField( 'Default channel',    default=0      );
	booted = models.BooleanField( 'Boot Server',        default = True );

	def getServerObject( self ):
		return mmServer( self.srvid, MumbleCtlBase.newInstance( self.dbus ), self.name );

	def __unicode__( self ):
		return u'Murmur "%s" (%d)' % ( self.name, self.srvid );
	
	def save( self, dontConfigureMurmur=False ):
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing servers.
			return models.Model.save( self );

		# check if this server already exists, if not call newServer and set my srvid first

		ctl = MumbleCtlBase.newInstance( self.dbus );
		if self.id is None:
			self.srvid = ctl.newServer();

		ctl.setConf( self.srvid,     'host',                socket.gethostbyname( self.addr ) );
		ctl.setConf( self.srvid,     'registername',        self.name );
		ctl.setConf( self.srvid,     'registerurl',         self.url );
		ctl.setConf( self.srvid,     'welcometext',         self.motd );
		ctl.setConf( self.srvid,     'password',            self.passwd );
		ctl.setConf( self.srvid,     'certificate',         self.sslcrt );
		ctl.setConf( self.srvid,     'key',                 self.sslkey );
		ctl.setConf( self.srvid,     'obfuscate',           str(self.obfsc).lower() );
		ctl.setConf( self.srvid,     'playername',          self.player );
		ctl.setConf( self.srvid,     'channelname',         self.channel );
		ctl.setConf( self.srvid,     'defaultchannel',      str(self.defchan) );
		
		
		if self.port is not None:
			ctl.setConf( self.srvid, 'port',                str(self.port) );
		else:
			ctl.setConf( self.srvid, 'port',                '' );
		
		if self.users is not None:
			ctl.setConf( self.srvid, 'users',               str(self.users) );
		else:
			ctl.setConf( self.srvid, 'users',               '' );
		
		if self.bwidth is not None:
			ctl.setConf( self.srvid, 'bandwidth',           str(self.bwidth) );
		else:
			ctl.setConf( self.srvid, 'bandwidth',           '' );
		
		# registerHostname needs to take the port no into account
		if self.port and self.port != 64738:
			ctl.setConf( self.srvid, 'registerhostname',    "%s:%d" % ( self.addr, self.port ) );
		else:
			ctl.setConf( self.srvid, 'registerhostname',    self.addr );

		if self.supw:
			ctl.setSuperUserPassword( self.srvid, self.supw );
			self.supw = '';
		
		if self.booted != ctl.isBooted( self.srvid ):
			if self.booted:
				ctl.start( self.srvid );
			else:
				ctl.stop( self.srvid );
		
		# Now allow django to save the record set
		return models.Model.save( self );
	
	def isUserAdmin( self, user ):
		if user.is_authenticated():
			try:
				return self.mumbleuser_set.get( owner=user ).getAdmin();
			except MumbleUser.DoesNotExist:
				return False;
		return False;

	def deleteServer( self ):
		# Unregister this player in Murmur via ctroller.
		#print MumbleCtlBase.newInstance()
		MumbleCtlBase.newInstance( self.dbus ).deleteServer(self.srvid)

	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].deleteServer();

class MumbleUser( models.Model ):
	mumbleid = models.IntegerField( 'Mumble player_id', editable = False, default = -1 );
	name     = models.CharField(    'User name and Login', max_length = 200 );
	password = models.CharField(    'Login password',      max_length = 200, blank=True );
	server   = models.ForeignKey(   Mumble );
	owner    = models.ForeignKey(   User, null=True, blank=True   );
	isAdmin  = models.BooleanField( 'Admin on root channel', default = False );

	def __unicode__( self ):
		return u"Mumble user %s on %s owned by Django user %s" % ( self.name, self.server, self.owner );
	
	def save( self, dontConfigureMurmur=False ):
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing players.
			return models.Model.save( self );
		
		# Before the record set is saved, update Murmur via ctroller.
		ctl = MumbleCtlBase.newInstance( self.server.dbus );

		if self.id is None:
			# This is a new user record, so Murmur doesn't know about it yet
			self.mumbleid = ctl.registerPlayer(self.server.srvid, self.name);
		
		# Update user's registration
		if self.password:
			if self.owner:
				email = self.owner.email
			else:
				email = settings.DEFAULT_FROM_EMAIL;
			
			ctl.setRegistration(
				self.server.srvid,
				self.mumbleid,
				self.name,
				email,
				self.password
				);
			
			# Don't save the users' passwords, we don't need them anyway
			self.password = '';
		
		self.setAdmin( self.isAdmin );
		
		# Now allow django to save the record set
		return models.Model.save( self );
	
	
	def getAdmin( self ):
		# Get ACL of root Channel, get the admin group and see if I'm in it
		acl = mmACL( 0, MumbleCtlBase.newInstance( self.server.dbus ).getACL(self.server.srvid, 0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ValueError( "The admin group was not found in the ACL's groups list!" );
		return self.mumbleid in acl.admingroup['add'];
	
	def setAdmin( self, value ):
		# Get ACL of root Channel, get the admin group and see if I'm in it
		ctl = MumbleCtlBase.newInstance( self.server.dbus );
		acl = mmACL( 0, ctl.getACL(self.server.srvid, 0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ValueError( "The admin group was not found in the ACL's groups list!" );
		
		if value != ( self.mumbleid in acl.admingroup['add'] ):
			if value:
				acl.admingroup['add'].append( self.mumbleid );
			else:
				acl.admingroup['add'].remove( self.mumbleid );
		
		ctl.setACL(self.server.srvid, acl);
		return value;
	
	def getTexture( self ):
		return MumbleCtlBase.newInstance( self.server.dbus ).getTexture(self.server.srvid, self.mumbleid);
	
	def setTexture( self, infile ):
		MumbleCtlBase.newInstance( self.server.dbus ).setTexture(self.server.srvid, self.mumbleid, infile)

	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].unregister();
	
	def unregister( self ):
		# Unregister this player in Murmur via dbus.
		MumbleCtlBase.newInstance( self.server.dbus ).unregisterPlayer(self.server.srvid, self.mumbleid)

	def __setattr__( self, name, value ):
		if name == 'server':
			if self.id is not None and self.server != value:
				raise AttributeError( "This field must not be updated once the Record has been saved." );
		
		models.Model.__setattr__( self, name, value );


from django.db.models import signals

signals.pre_delete.connect( Mumble.pre_delete_listener,     sender=Mumble     );
signals.pre_delete.connect( MumbleUser.pre_delete_listener, sender=MumbleUser );




