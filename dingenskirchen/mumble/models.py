from django.contrib.auth.models import User
from django.db import models

from mmobjects import mmServer

import dbus
import socket

class Mumble( models.Model ):
	name   = models.CharField(    'Server Name',     max_length = 200 );
	dbus   = models.CharField(    'DBus base',       max_length = 200, default = 'net.sourceforge.mumble.murmur' );
	srvid  = models.IntegerField( 'Server ID',       editable = False );
	addr   = models.CharField(    'Server Address',  max_length = 200 );
	port   = models.IntegerField( 'Server Port',                       blank = True, null = True  );
	url    = models.CharField(    'Website URL',     max_length = 200, blank = True );
	motd   = models.TextField(    'Welcome Message',                   blank = True );
	passwd = models.CharField(    'Server Password', max_length = 200, blank = True );
	users  = models.IntegerField( 'Max. Users',                        blank = True, null = True );
	bwidth = models.IntegerField( 'Bandwidth [Bps]',                   blank = True, null = True );
	sslcrt = models.CharField(    'SSL Certificate', max_length = 200, blank = True );
	sslkey = models.CharField(    'SSL Key',         max_length = 200, blank = True );
	booted = models.BooleanField( 'Boot Server',     default = True );
	
	def getDbusMeta( self ):
		return dbus.SystemBus().get_object( self.dbus, '/' );
	
	def getDbusObject( self ):
		"Connects to DBus and returns an mmServer object representing this Murmur instance."
		bus    = dbus.SystemBus();
		murmur = bus.get_object( self.dbus, '/' );
		
		if self.srvid not in murmur.getBootedServers():
			raise Exception, 'No murmur process with the given server ID (%d) is running and attached to system dbus under %s.' % ( self.srvid, self.dbus );
		
		return bus.get_object( self.dbus, '/%d' % self.srvid );
	
	def getServerObject( self ):
		return mmServer( self.srvid, self.getDbusObject(), self.name );
	
	def __unicode__( self ):
		return u'Murmur "%s" (%d)' % ( self.name, self.srvid );
	
	def save( self ):
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
		murmur.setConf( srvid,     'sslCert',             self.sslcrt );
		murmur.setConf( srvid,     'sslKey',              self.sslkey );
		
		if self.port is not None:
			murmur.setConf( srvid, 'port',                str(self.port) );
		else:
			murmur.setConf( srvid, 'port',                '' );
		
		if self.users is not None:
			murmur.setConf( srvid, 'users',               str(self.users) );
		else:
			murmur.setConf( srvid, 'users',               '' );
		
		if self.bwidth is not None:
			murmur.setConf( srvid, 'bandwidth',           str(self.port) );
		else:
			murmur.setConf( srvid, 'bandwidth',           '' );
		
		# registerHostname needs to take the port no into account
		if self.port and self.port != 64738:
			murmur.setConf( srvid, 'registerHostname',    "%s:%d" % ( self.addr, self.port ) );
		else:
			murmur.setConf( srvid, 'registerHostname',    self.addr );
		
		if self.booted != murmur.isBooted( dbus.Int32(self.srvid) ):
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
	owner    = models.ForeignKey(   User   );
	
	def __unicode__( self ):
		return u"Mumble user %s on %s owned by Django user %s" % ( self.name, self.server, self.owner );
	
	def save( self ):
		# Before the record set is saved, update Murmur via dbus.
		murmur = self.server.getDbusObject();
		
		if self.id is None:
			# This is a new user record, so Murmur doesn't know about it yet
			self.mumbleid = murmur.registerPlayer( dbus.String( self.name ) );
		
		# Update user's registration
		murmur.setRegistration(
			dbus.Int32(  self.mumbleid ),
			dbus.String( self.name ),
			dbus.String( self.owner.email ),
			dbus.String( self.password )
			);
		
		# Don't save the users' passwords, we don't need them anyway
		self.password = '';
		
		# Now allow django to save the record set
		return models.Model.save( self );
	
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




