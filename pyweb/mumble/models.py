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

import dbus
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
	
	def getDbusMeta( self ):
		return dbus.Interface( dbus.SystemBus().get_object( self.dbus, '/' ), 'net.sourceforge.mumble.Meta' );
	
	def getDbusObject( self ):
		"Connects to DBus and returns an mmServer object representing this Murmur instance."
		bus    = dbus.SystemBus();
		murmur = dbus.Interface( bus.get_object( self.dbus, '/' ), 'net.sourceforge.mumble.Meta');
		
		if self.srvid not in murmur.getBootedServers():
			raise Exception, 'No murmur process with the given server ID (%d) is running and attached to system dbus under %s.' % ( self.srvid, self.dbus );
		
		return dbus.Interface( bus.get_object( self.dbus, '/%d' % self.srvid ), 'net.sourceforge.mumble.Murmur' );
	
	def getServerObject( self ):
		return mmServer( self.srvid, self.getDbusObject(), self.name );
	
	def __unicode__( self ):
		return u'Murmur "%s" (%d)' % ( self.name, self.srvid );
	
	def save( self, dontConfigureMurmur=False ):
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing servers.
			return models.Model.save( self );
		
		# Prior to saving the model, connect to murmur via dbus and update its settings.
		murmur = self.getDbusMeta();
		
		# check if this server already exists, if not call newServer and set my srvid first
		if self.id is None:
			self.srvid = murmur.newServer();
		
		srvid = dbus.Int32( self.srvid );
		
		murmur.setConf( srvid,     'host',                socket.gethostbyname( self.addr ) );
		murmur.setConf( srvid,     'registername',        self.name );
		murmur.setConf( srvid,     'registerurl',         self.url );
		murmur.setConf( srvid,     'welcometext',         self.motd );
		murmur.setConf( srvid,     'password',            self.passwd );
		murmur.setConf( srvid,     'certificate',         self.sslcrt );
		murmur.setConf( srvid,     'key',                 self.sslkey );
		murmur.setConf( srvid,     'obfuscate',           str(self.obfsc).lower() );
		murmur.setConf( srvid,     'playername',          self.player );
		murmur.setConf( srvid,     'channelname',         self.channel );
		murmur.setConf( srvid,     'defaultchannel',      str(self.defchan) );
		
		
		if self.port is not None:
			murmur.setConf( srvid, 'port',                str(self.port) );
		else:
			murmur.setConf( srvid, 'port',                '' );
		
		if self.users is not None:
			murmur.setConf( srvid, 'users',               str(self.users) );
		else:
			murmur.setConf( srvid, 'users',               '' );
		
		if self.bwidth is not None:
			murmur.setConf( srvid, 'bandwidth',           str(self.bwidth) );
		else:
			murmur.setConf( srvid, 'bandwidth',           '' );
		
		# registerHostname needs to take the port no into account
		if self.port and self.port != 64738:
			murmur.setConf( srvid, 'registerhostname',    "%s:%d" % ( self.addr, self.port ) );
		else:
			murmur.setConf( srvid, 'registerhostname',    self.addr );
		
		if self.supw:
			murmur.setSuperUserPassword( srvid, self.supw );
			self.supw = '';
		
		if self.booted != murmur.isBooted( srvid ):
			if self.booted:
				murmur.start( srvid );
			else:
				murmur.stop( srvid );
		
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
		srvid = dbus.Int32( self.srvid );
		murmur = self.getDbusMeta();
		if murmur.isBooted( srvid ):
			murmur.stop( srvid );
		murmur.deleteServer( srvid );
	
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
		
		# Before the record set is saved, update Murmur via dbus.
		murmur = self.server.getDbusObject();
		
		if self.id is None:
			# This is a new user record, so Murmur doesn't know about it yet
			self.mumbleid = murmur.registerPlayer( dbus.String( self.name ) );
		
		# Update user's registration
		if self.password:
			if self.owner:
				email = self.owner.email
			else:
				email = settings.DEFAULT_FROM_EMAIL;
			
			murmur.setRegistration(
				dbus.Int32(  self.mumbleid  ),
				dbus.String( self.name      ),
				dbus.String( email          ),
				dbus.String( self.password  )
				);
			
			# Don't save the users' passwords, we don't need them anyway
			self.password = '';
		
		self.setAdmin( self.isAdmin );
		
		# Now allow django to save the record set
		return models.Model.save( self );
	
	
	def getAdmin( self ):
		# Get ACL of root Channel, get the admin group and see if I'm in it
		bus = self.server.getDbusObject();
		acl = mmACL( 0, bus.getACL(0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ValueError( "The admin group was not found in the ACL's groups list!" );
		return self.mumbleid in acl.admingroup['add'];
	
	def setAdmin( self, value ):
		# Get ACL of root Channel, get the admin group and see if I'm in it
		bus = self.server.getDbusObject();
		acl = mmACL( 0, bus.getACL(0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ValueError( "The admin group was not found in the ACL's groups list!" );
		
		if value != ( self.mumbleid in acl.admingroup['add'] ):
			if value:
				acl.admingroup['add'].append( dbus.Int32(self.mumbleid) );
			else:
				acl.admingroup['add'].remove( self.mumbleid );
		
		bus.setACL( *acl.pack() );
		return value;
	
	def getTexture( self ):
		murmur = self.server.getDbusObject();
		texture = murmur.getTexture( dbus.Int32( self.mumbleid ) );
		if len(texture) == 0:
			raise ValueError( "No Texture has been set." );
		# this returns a list of bytes.
		# first 4 bytes: Length of uncompressed string, rest: compressed data
		orig_len = ( texture[0] << 24 ) | ( texture[1] << 16 ) | ( texture[2] << 8 ) | ( texture[3] );
		# convert rest to string and run decompress
		bytestr = "";
		for byte in texture[4:]:
			bytestr += pack( "B", int(byte) );
		decompressed = decompress( bytestr );
		# iterate over 4 byte chunks of the string
		imgdata = "";
		for idx in range( 0, orig_len, 4 ):
			# read 4 bytes = BGRA and convert to RGBA
			bgra = unpack( "4B", decompressed[idx:idx+4] );
			imgdata += pack( "4B",  bgra[2], bgra[1], bgra[0], bgra[3] );
		# return an 600x60 RGBA image object created from the data
		return Image.fromstring( "RGBA", ( 600, 60 ), imgdata );
	
	def setTexture( self, infile ):
		# open image, convert to RGBA, and resize to 600x60
		img = Image.open( infile ).convert( "RGBA" ).transform( ( 600, 60 ), Image.EXTENT, ( 0, 0, 600, 60 ) );
		# iterate over the list and pack everything into a string
		bgrastring = "";
		for ent in list( img.getdata() ):
			# ent is in RGBA format, but Murmur wants BGRA (ARGB inverse), so stuff needs
			# to be reordered when passed to pack()
			bgrastring += pack( "4B",  ent[2], ent[1], ent[0], ent[3] );
		# compress using zlib
		compressed = compress( bgrastring );
		# pack the original length in 4 byte big endian, and concat the compressed
		# data to it to emulate qCompress().
		texture = pack( ">L", len(bgrastring) ) + compressed;
		# finally call murmur and set the texture
		murmur = self.server.getDbusObject();
		murmur.setTexture( dbus.Int32( self.mumbleid ), texture );

	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].unregister();
	
	def unregister( self ):
		# Unregister this player in Murmur via dbus.
		murmur = self.server.getDbusObject();
		murmur.unregisterPlayer( dbus.Int32( self.mumbleid ) );
	
	def __setattr__( self, name, value ):
		if name == 'server':
			if self.id is not None and self.server != value:
				raise AttributeError( "This field must not be updated once the Record has been saved." );
		
		models.Model.__setattr__( self, name, value );


from django.db.models import signals

signals.pre_delete.connect( Mumble.pre_delete_listener,     sender=Mumble     );
signals.pre_delete.connect( MumbleUser.pre_delete_listener, sender=MumbleUser );




