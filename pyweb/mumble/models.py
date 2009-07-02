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

import socket
from PIL         import Image
from struct      import pack, unpack
from zlib        import compress, decompress

from django.contrib.auth.models import User
from django.db   import models

from django.conf import settings

from mmobjects   import *
from mctl        import *


class Mumble( models.Model ):
	name   = models.CharField(    'Server Name',        max_length = 200 );
	dbus   = models.CharField(    'DBus or ICE base',   max_length = 200, default = settings.DEFAULT_CONN );
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
	
	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs );
		self._ctl      = None;
		self._channels = None;
		self._rootchan = None;
	
	def __unicode__( self ):
		return u'Murmur "%s" (%d)' % ( self.name, self.srvid );
	
	
	is_server  = True;
	is_channel = False;
	is_player  = False;
	
	
	# Ctl instantiation
	def getCtl( self ):
		if not self._ctl:
			self._ctl = MumbleCtlBase.newInstance( self.dbus );
		return self._ctl;
	
	ctl = property( getCtl, None );
	
	
	def save( self, dontConfigureMurmur=False ):
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing servers.
			return models.Model.save( self );
		
		# check if this server already exists, if not call newServer and set my srvid first
		
		if self.id is None:
			self.srvid = self.ctl.newServer();
		
		self.ctl.setConf( self.srvid,     'host',                socket.gethostbyname( self.addr ) );
		self.ctl.setConf( self.srvid,     'registername',        self.name );
		self.ctl.setConf( self.srvid,     'registerurl',         self.url );
		self.ctl.setConf( self.srvid,     'welcometext',         self.motd );
		self.ctl.setConf( self.srvid,     'password',            self.passwd );
		self.ctl.setConf( self.srvid,     'certificate',         self.sslcrt );
		self.ctl.setConf( self.srvid,     'key',                 self.sslkey );
		self.ctl.setConf( self.srvid,     'obfuscate',           str(self.obfsc).lower() );
		self.ctl.setConf( self.srvid,     'playername',          self.player );
		self.ctl.setConf( self.srvid,     'channelname',         self.channel );
		self.ctl.setConf( self.srvid,     'defaultchannel',      str(self.defchan) );
		
		
		if self.port is not None:
			self.ctl.setConf( self.srvid, 'port',                str(self.port) );
		else:
			self.ctl.setConf( self.srvid, 'port',                '' );
		
		if self.users is not None:
			self.ctl.setConf( self.srvid, 'users',               str(self.users) );
		else:
			self.ctl.setConf( self.srvid, 'users',               '' );
		
		if self.bwidth is not None:
			self.ctl.setConf( self.srvid, 'bandwidth',           str(self.bwidth) );
		else:
			self.ctl.setConf( self.srvid, 'bandwidth',           '' );
		
		# registerHostname needs to take the port no into account
		if self.port and self.port != settings.MUMBLE_DEFAULT_PORT:
			self.ctl.setConf( self.srvid, 'registerhostname',    "%s:%d" % ( self.addr, self.port ) );
		else:
			self.ctl.setConf( self.srvid, 'registerhostname',    self.addr );
		
		if self.supw:
			self.ctl.setSuperUserPassword( self.srvid, self.supw );
			self.supw = '';
		
		if self.booted != self.ctl.isBooted( self.srvid ):
			if self.booted:
				self.ctl.start( self.srvid );
			else:
				self.ctl.stop( self.srvid );
		
		# Now allow django to save the record set
		return models.Model.save( self );
	
	
	def isUserAdmin( self, user ):
		if user.is_authenticated():
			try:
				return self.mumbleuser_set.get( owner=user ).getAdmin();
			except MumbleUser.DoesNotExist:
				return False;
		return False;
	
	
	# Deletion handler
	def deleteServer( self ):
		# Unregister this player in Murmur via ctroller.
		self.ctl.deleteServer(self.srvid)
	
	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].deleteServer();
	
	
	# Channel lists: flat list
	def getChannels( self ):
		if self._channels is None:
			self._channels = {};
			chanlist = self.ctl.getChannels(self.srvid);
			links = {};
			
			# sometimes, ICE seems to return the Channel list in a weird order.
			# itercount prevents infinite loops.
			itercount = 0;
			maxiter   = len(chanlist) * 3;
			while len(chanlist) and itercount < maxiter:
				itercount += 1;
				for theChan in chanlist:
					# Channels - Fields: 0 = ID, 1 = Name, 2 = Parent-ID, 3 = Links
					if( theChan[2] == -1 ):
						# No parent
						self._channels[theChan[0]] = mmChannel( self, theChan );
					elif theChan[2] in self.channels:
						# parent already known
						self._channels[theChan[0]] = mmChannel( self, theChan, self.channels[theChan[2]] );
					else:
						continue;
					
					chanlist.remove( theChan );
					
					self._channels[theChan[0]].serverId = self.id;
					
					# process links - if the linked channels are known, link; else save their ids to link later
					for linked in theChan[3]:
						if linked in self._channels:
							self._channels[theChan[0]].linked.append( self._channels[linked] );
						else:
							if linked not in links:
								links[linked] = list();
							links[linked].append( self._channels[theChan[0]] );
					
					# check if earlier round trips saved channel ids to be linked to the current channel
					if theChan[0] in links:
						for targetChan in links[theChan[0]]:
							targetChan.linked.append( self._channels[theChan[0]] );
			
			self._channels[0].name = self.name;
			
			self.players = {};
			for thePlayer in self.ctl.getPlayers(self.srvid):
				# Players - Fields: 0 = UserID, 6 = ChannelID
				self.players[ thePlayer[0] ] = mmPlayer( self, thePlayer, self._channels[ thePlayer[6] ] );
			
			self._channels[0].sort();
		
		return self._channels;
	
	channels = property( getChannels, None );
	rootchan = property( lambda self: self.channels[0], None );
	
	def getURL( self, forUser = None ):
		# mumble://username@host:port/
		userstr = "";
		if forUser is not None:
			userstr = "%s@" % forUser.name;
		
		if self.port != settings.MUMBLE_DEFAULT_PORT:
			return "mumble://%s%s:%d/" % ( userstr, self.addr, self.port );
		
		return "mumble://%s%s/" % ( userstr, self.addr );
	
	connecturl = property( getURL, None );
	
	version = property( lambda self: self.ctl.getVersion(), None );



class MumbleUser( models.Model ):
	mumbleid = models.IntegerField( 'Mumble player_id', editable = False, default = -1 );
	name     = models.CharField(    'User name and Login', max_length = 200 );
	password = models.CharField(    'Login password',      max_length = 200, blank=True );
	server   = models.ForeignKey(   Mumble );
	owner    = models.ForeignKey(   User, null=True, blank=True   );
	isAdmin  = models.BooleanField( 'Admin on root channel', default = False );
	
	
	is_server  = False;
	is_channel = False;
	is_player  = True;
	
	
	def __unicode__( self ):
		return u"Mumble user %s on %s owned by Django user %s" % ( self.name, self.server, self.owner );
	
	
	
	def save( self, dontConfigureMurmur=False ):
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing players.
			return models.Model.save( self );
		
		# Before the record set is saved, update Murmur via controller.
		ctl = self.server.ctl;
		
		if self.id is None:
			# This is a new user record, so Murmur doesn't know about it yet
			if len( ctl.getRegisteredPlayers( self.server.srvid, self.name ) ) > 0:
				raise ValueError( "Another player already registered that name." );
			self.mumbleid = ctl.registerPlayer( self.server.srvid, self.name );
		
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
	
	
	# Admin handlers
	
	def getAdmin( self ):
		# Get ACL of root Channel, get the admin group and see if I'm in it
		acl = mmACL( 0, self.server.ctl.getACL(self.server.srvid, 0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ValueError( "The admin group was not found in the ACL's groups list!" );
		return self.mumbleid in acl.admingroup['add'];
	
	def setAdmin( self, value ):
		# Get ACL of root Channel, get the admin group and see if I'm in it
		ctl = self.server.ctl;
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
	
	
	# Texture handlers
	
	def getTexture( self ):
		return self.server.ctl.getTexture(self.server.srvid, self.mumbleid);
	
	def setTexture( self, infile ):
		self.server.ctl.setTexture(self.server.srvid, self.mumbleid, infile)
	
	
	# Deletion handler
	
	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].unregister();
	
	def unregister( self ):
		# Unregister this player in Murmur via dbus.
		self.server.ctl.unregisterPlayer(self.server.srvid, self.mumbleid)
	
	
	# "server" field protection
	
	def __setattr__( self, name, value ):
		if name == 'server':
			if self.id is not None and self.server != value:
				raise AttributeError( "This field must not be updated once the Record has been saved." );
		
		models.Model.__setattr__( self, name, value );




from django.db.models import signals

signals.pre_delete.connect( Mumble.pre_delete_listener,     sender=Mumble     );
signals.pre_delete.connect( MumbleUser.pre_delete_listener, sender=MumbleUser );




