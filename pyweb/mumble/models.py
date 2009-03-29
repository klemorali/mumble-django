""" This file is part of the mumble-django application.
    
    Copyright (C) 2009, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 
    All rights reserved.
 
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
 
    - Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    - Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    - Neither the name of the Mumble Developers nor the names of its
      contributors may be used to endorse or promote products derived from this
      software without specific prior written permission.
 
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from django.contrib.auth.models import User
from django.db import models

from mmobjects import mmServer, mmACL

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
		murmur.setConf( srvid,     'registerName',        self.name );
		murmur.setConf( srvid,     'registerUrl',         self.url );
		murmur.setConf( srvid,     'welcometext',         self.motd );
		murmur.setConf( srvid,     'password',            self.passwd );
		murmur.setConf( srvid,     'certificate',         self.sslcrt );
		murmur.setConf( srvid,     'key',                 self.sslkey );
		
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
			murmur.setConf( srvid, 'registerHostname',    "%s:%d" % ( self.addr, self.port ) );
		else:
			murmur.setConf( srvid, 'registerHostname',    self.addr );
		
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
	password = models.CharField(    'Login password',      max_length = 200 );
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
			murmur.setRegistration(
				dbus.Int32(  self.mumbleid    ),
				dbus.String( self.name        ),
				dbus.String( self.owner.email ),
				dbus.String( self.password    )
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
	
	
	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].unregister();
	
	def unregister( self ):
		# Unregister this player in Murmur via dbus.
		murmur = self.server.getDbusObject();
		murmur.unregisterPlayer( dbus.Int32( self.mumbleid ) );




from django.db.models import signals

signals.pre_delete.connect( Mumble.pre_delete_listener,     sender=Mumble     );
signals.pre_delete.connect( MumbleUser.pre_delete_listener, sender=MumbleUser );




