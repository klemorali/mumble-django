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

from django.utils.translation	import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db			import models
from django.db.models		import signals
from django.conf		import settings

from mmobjects			import *
from mctl			import *



class Mumble( models.Model ):
	""" Represents a Murmur server instance.
	
	    All configurable settings are represented by a field in this model. To change the
	    settings, just update the appropriate field and call the save() method.
	
	    To set up a new server instance, instanciate this Model. The first field you should
	    define is the "dbus" field, which tells the connector subsystem how to connect to
	    the Murmurd master process. Set this to the appropriate DBus service name or the
	    Ice proxy string.
	
	    When an instance of this model is deleted, the according server instance will be
	    deleted as well.
	"""
	
	name    = models.CharField(    _('Server Name'),        max_length = 200 );
	dbus    = models.CharField(    _('DBus or ICE base'),   max_length = 200, default = settings.DEFAULT_CONN, help_text=_("Examples: 'net.sourceforge.mumble.murmur' for DBus or 'Meta:tcp -h 127.0.0.1 -p 6502' for Ice.") );
	srvid   = models.IntegerField( _('Server ID'),          editable = False );
	addr    = models.CharField(    _('Server Address'),     max_length = 200, help_text=_("Hostname or IP address to bind to. You should use a hostname here, because it will appear on the global server list.") );
	port    = models.IntegerField( _('Server Port'),        help_text=_("Port number to bind to. Use -1 to auto assign one."), default=settings.MUMBLE_DEFAULT_PORT );
	url     = models.CharField(    _('Website URL'),        max_length = 200, blank = True );
	motd    = models.TextField(    _('Welcome Message'),                      blank = True );
	passwd  = models.CharField(    _('Server Password'),    max_length = 200, blank = True, help_text=_("Password required to join. Leave empty for public servers.") );
	supw    = models.CharField(    _('Superuser Password'), max_length = 200, blank = True );
	users   = models.IntegerField( _('Max. Users'),                           blank = True, null = True );
	bwidth  = models.IntegerField( _('Bandwidth [Bps]'),                      blank = True, null = True );
	sslcrt  = models.TextField(    _('SSL Certificate'),                      blank = True );
	sslkey  = models.TextField(    _('SSL Key'),            blank = True    );
	obfsc   = models.BooleanField( _('IP Obfuscation'),     default = False,  help_text=_("If on, IP adresses of the clients are not logged.") );
	player  = models.CharField(    _('Player name regex'),  max_length=200,   default=r'[-=\w\[\]\{\}\(\)\@\|\.]+'   );
	channel = models.CharField(    _('Channel name regex'), max_length=200,   default=r'[ \-=\w\#\[\]\{\}\(\)\@\|]+' );
	defchan = models.IntegerField( _('Default channel'),    default=0,        help_text=_("Enter the ID of the default channel here. The Channel viewer displays the ID to server admins on the channel detail page."));
	booted  = models.BooleanField( _('Boot Server'),        default = True  );
	
	class Meta:
		unique_together     = ( ( 'dbus', 'srvid' ), ( 'addr', 'port' ), );
		verbose_name        = _('Server instance');
		verbose_name_plural = _('Server instances');
	
	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs );
		self._ctl      = None;
		self._channels = None;
		self._rootchan = None;
	
	def __unicode__( self ):
		if not self.id:
			return u'Murmur "%s" (NOT YET CREATED)' % self.name;
		return u'Murmur "%s" (%d)' % ( self.name, self.srvid );
	
	
	users_regged = property( lambda self: self.mumbleuser_set.count(),           doc="Number of registered users." );
	users_online = property( lambda self: len(self.ctl.getPlayers(self.srvid)),  doc="Number of online users." );
	channel_cnt  = property( lambda self: len(self.ctl.getChannels(self.srvid)), doc="Number of channels." );
	is_public    = property( lambda self: self.passwd == '',                     doc="False if a password is needed to join this server." );
	
	is_server  = True;
	is_channel = False;
	is_player  = False;
	
	
	# Ctl instantiation
	def getCtl( self ):
		"""Instantiate and return a MumbleCtl object for this server.
		
		Only one instance will be created, and reused on subsequent calls.
		"""
		if not self._ctl:
			self._ctl = MumbleCtlBase.newInstance( self.dbus );
		return self._ctl;
	
	ctl = property( getCtl, doc="Get a Control object for this server. The ctl is cached for later reuse." );
	
	
	def save( self, dontConfigureMurmur=False ):
		"""
		Save the options configured in this model instance not only to Django's database,
		but to Murmur as well.
		"""
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing servers.
			return models.Model.save( self );
		
		# check if this server already exists, if not call newServer and set my srvid first
		
		if self.id is None:
			self.srvid = self.ctl.newServer();
		
		if self.port == -1:
			self.port = max( [ rec['port'] for rec in Mumble.objects.values('port') ] ) + 1;
		
		if self.port < 1 or self.port >= 2**16:
			raise ValueError( _("Port number %(portno)d is not within the allowed range %(minrange)d - %(maxrange)d") % {
				'portno': self.port,
				'minrange': 1,
				'maxrange': 2**16,
				});
		
		self.ctl.setConf( self.srvid,     'host',                socket.gethostbyname( self.addr ) );
		self.ctl.setConf( self.srvid,     'port',                str(self.port) );
		self.ctl.setConf( self.srvid,     'registername',        self.name );
		self.ctl.setConf( self.srvid,     'registerurl',         self.url );
		self.ctl.setConf( self.srvid,     'welcometext',         self.motd );
		self.ctl.setConf( self.srvid,     'password',            self.passwd );
		self.ctl.setConf( self.srvid,     'certificate',         self.sslcrt );
		self.ctl.setConf( self.srvid,     'key',                 self.sslkey );
		self.ctl.setConf( self.srvid,     'obfuscate',           str(self.obfsc).lower() );
		
		if self.ctl.getVersion()[:2] == ( 1, 2 ):
			self.ctl.setConf( self.srvid,     'username',    self.player );
		else:
			self.ctl.setConf( self.srvid,     'playername',  self.player );
		
		self.ctl.setConf( self.srvid,     'channelname',         self.channel );
		self.ctl.setConf( self.srvid,     'defaultchannel',      str(self.defchan) );
		
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
	
	
	def configureFromMurmur( self ):
		default = self.ctl.getDefaultConf();
		conf    = self.ctl.getAllConf( self.srvid );
		
		def find_in_dicts( keys, valueIfNotFound=None ):
			if not isinstance( keys, tuple ):
				keys = ( keys, );
			
			for keyword in keys:
				if keyword in conf:
					return conf[keyword];
			
			for keyword in keys:
				keyword = keyword.lower();
				if keyword in default:
					return default[keyword];
			
			return valueIfNotFound;
		
		servername = find_in_dicts( "registername", "noname" );
		if not servername:
			# RegistrationName was found in the dicts, but is an empty string
			servername = "noname";
		
		addr =  find_in_dicts( ( "registerhostname", "host" ), "0.0.0.0" );
		if addr.find( ':' ) != -1:
			# The addr is a hostname which actually contains a port number, but we already got that from
			# the port field, so we can simply drop it.
			addr = addr.split(':')[0];
		
		self.name    =  servername;
		self.addr    =  addr;
		self.port    =  find_in_dicts( "port"        );
		self.url     =  find_in_dicts( "registerurl" );
		self.motd    =  find_in_dicts( "welcometext" );
		self.passwd  =  find_in_dicts( "password"    );
		self.supw    =  '';
		self.users   =  find_in_dicts( "users"       );
		self.bwidth  =  find_in_dicts( "bandwidth"   );
		self.sslcrt  =  find_in_dicts( "certificate" );
		self.sslkey  =  find_in_dicts( "key"         );
		self.obfsc   =  bool( find_in_dicts( 'obfuscate' ) );
		
		pldefault = self._meta.get_field_by_name('player')[0].default;
		if self.ctl.getVersion()[:2] == ( 1, 2 ):
			self.player  =  find_in_dicts( ( 'username', 'playername' ), pldefault );
		else:
			self.player  =  find_in_dicts( 'playername', pldefault );
		
		chdefault = self._meta.get_field_by_name('channel')[0].default;
		self.channel =  find_in_dicts( 'channelname', chdefault );
		
		self.defchan =  int( find_in_dicts( 'defaultchannel', 0 ) );
		self.booted  =  ( self.srvid in self.ctl.getBootedServers() );
		
		self.save( dontConfigureMurmur=True );
	
	
	def readUsersFromMurmur( self, verbose=0 ):
		if not self.booted:
			raise SystemError( "This murmur instance is not currently running, can't sync." );
		
		players = self.ctl.getRegisteredPlayers(self.srvid);
		
		for playerdata in players:
			if playerdata[0] == 0: # Skip SuperUsers
				continue;
			if verbose > 1:
				print "Checking Player with id %d and name '%s'." % ( int(playerdata[0]), playerdata[1] );
			
			try:
				playerinstance = MumbleUser.objects.get( server=self, mumbleid=playerdata[0] );
			
			except MumbleUser.DoesNotExist:
				if verbose:
					print 'Found new Player "%s".' % playerdata[1];
				
				playerinstance = MumbleUser(
					mumbleid = playerdata[0],
					name     = playerdata[1],
					password = '',
					server   = self,
					owner    = None
					);
			
			else:
				if verbose > 1:
					print "This player is already listed in the database.";
			
				playerinstance.name = playerdata[1];
			
			playerinstance.isAdmin = playerinstance.getAdmin();
			playerinstance.save( dontConfigureMurmur=True );

	
	def isUserAdmin( self, user ):
		"""Determine if the given user is an admin on this server."""
		if user.is_authenticated():
			try:
				return self.mumbleuser_set.get( owner=user ).getAdmin();
			except MumbleUser.DoesNotExist:
				return False;
		return False;
	
	
	# Deletion handler
	def deleteServer( self ):
		"""Delete this server instance from Murmur."""
		self.ctl.deleteServer(self.srvid)
	
	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].deleteServer();
	
	
	# Channel list
	def getChannels( self ):
		"""Query the channels from Murmur and create a tree structure.
		
		Again, this will only be done for the first call to this function. Subsequent
		calls will simply return the list created last time.
		"""
		if self._channels is None:
			self._channels = {};
			chanlist = self.ctl.getChannels(self.srvid).values();
			links = {};
			
			# sometimes, ICE seems to return the Channel list in a weird order.
			# itercount prevents infinite loops.
			itercount = 0;
			maxiter   = len(chanlist) * 3;
			while len(chanlist) and itercount < maxiter:
				itercount += 1;
				for theChan in chanlist:
					# Channels - Fields: 0 = ID, 1 = Name, 2 = Parent-ID, 3 = Links
					if( theChan.parent == -1 ):
						# No parent
						self._channels[theChan.id] = mmChannel( self, theChan );
					elif theChan.parent in self.channels:
						# parent already known
						self._channels[theChan.id] = mmChannel( self, theChan, self.channels[theChan.parent] );
					else:
						continue;
					
					chanlist.remove( theChan );
					
					self._channels[theChan.id].serverId = self.id;
					
					# process links - if the linked channels are known, link; else save their ids to link later
					for linked in theChan.links:
						if linked in self._channels:
							self._channels[theChan.id].linked.append( self._channels[linked] );
						else:
							if linked not in links:
								links[linked] = list();
							links[linked].append( self._channels[theChan.id] );
					
					# check if earlier round trips saved channel ids to be linked to the current channel
					if theChan.id in links:
						for targetChan in links[theChan.id]:
							targetChan.linked.append( self._channels[theChan.id] );
			
			self._channels[0].name = self.name;
			
			self.players = {};
			for thePlayer in self.ctl.getPlayers(self.srvid):
				# Players - Fields: 0 = UserID, 6 = ChannelID
				self.players[ thePlayer[0] ] = mmPlayer( self, thePlayer, self._channels[ thePlayer[6] ] );
			
			self._channels[0].sort();
		
		return self._channels;
	
	channels = property( getChannels,                       doc="A convenience wrapper for getChannels()."    );
	rootchan = property( lambda self: self.channels[0],     doc="A convenience wrapper for getChannels()[0]." );
	
	def getURL( self, forUser = None ):
		"""Create an URL of the form mumble://username@host:port/ for this server."""
		userstr = "";
		if forUser is not None:
			userstr = "%s@" % forUser.name;
		
		versionstr = "version=%d.%d.%d" % tuple(self.version[0:3]);
		
		if self.port != settings.MUMBLE_DEFAULT_PORT:
			return "mumble://%s%s:%d/?%s" % ( userstr, self.addr, self.port, versionstr );
		
		return "mumble://%s%s/?%s" % ( userstr, self.addr, versionstr );
	
	connecturl = property( getURL,                          doc="A convenience wrapper for getURL()." );
	
	version = property( lambda self: self.ctl.getVersion(), doc="The version of Murmur."              );
	
	def as_dict( self ):
		return { 'name':   self.name,
			 'id':     self.id,
			 'root':   self.rootchan.as_dict()
			};



class MumbleUser( models.Model ):
	""" Represents a User account in Murmur.
	
	    To change an account, simply set the according field in this model and call the save()
	    method to update the account in Murmur and in Django's database. Note that, once saved
	    for the first time, the server field must not be changed. Attempting to do this will
	    result in an AttributeError. To move an account to a new server, recreate it on the
	    new server and delete the old model.
	
	    When you delete an instance of this model, the according user account will be deleted
	    in Murmur as well, after revoking the user's admin privileges.
	"""
	
	mumbleid = models.IntegerField(         _('Mumble player_id'),            editable = False, default = -1 );
	name     = models.CharField(            _('User name and Login'),         max_length = 200 );
	password = models.CharField(            _('Login password'),              max_length = 200, blank=True );
	server   = models.ForeignKey(   Mumble, verbose_name=_('Server instance') );
	owner    = models.ForeignKey(   User,   verbose_name=_('Account owner'),  null=True, blank=True   );
	isAdmin  = models.BooleanField(         _('Admin on root channel'),       default = False );
	
	class Meta:
		unique_together     = ( ( 'server', 'owner' ), ( 'server', 'mumbleid' ) );
		verbose_name        = _( 'User account'  );
		verbose_name_plural = _( 'User accounts' );
	
	is_server  = False;
	is_channel = False;
	is_player  = True;
	
	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs );
		self._registration = None;
	
	def __unicode__( self ):
		return _("Mumble user %(mu)s on %(srv)s owned by Django user %(du)s") % { 'mu': self.name, 'srv': self.server, 'du': self.owner };
	
	def save( self, dontConfigureMurmur=False ):
		"""Save the settings in this model to Murmur."""
		if dontConfigureMurmur:
			# skip murmur configuration, e.g. because we're inserting models for existing players.
			return models.Model.save( self );
		
		# Before the record set is saved, update Murmur via controller.
		ctl = self.server.ctl;
		
		if self.owner:
			email = self.owner.email;
		else:
			email = settings.DEFAULT_FROM_EMAIL;
		
		if self.id is None:
			# This is a new user record, so Murmur doesn't know about it yet
			if len( ctl.getRegisteredPlayers( self.server.srvid, self.name ) ) > 0:
				raise ValueError( _( "Another player already registered that name." ) );
			if not self.password:
				raise ValueError( _( "Cannot register player without a password!" ) );
			
			self.mumbleid = ctl.registerPlayer( self.server.srvid, self.name, email, self.password );
		
		# Update user's registration
		elif self.password:
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
		"""Get ACL of root Channel, get the admin group and see if this user is in it."""
		acl = mmACL( 0, self.server.ctl.getACL(self.server.srvid, 0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ReferenceError( _( "The admin group was not found in the ACL's groups list!" ) );
		return self.mumbleid in acl.admingroup['add'];
	
	def setAdmin( self, value ):
		"""Set or revoke this user's membership in the admin group on the root channel."""
		ctl = self.server.ctl;
		acl = mmACL( 0, ctl.getACL(self.server.srvid, 0) );
		
		if not hasattr( acl, "admingroup" ):
			raise ReferenceError( _( "The admin group was not found in the ACL's groups list!" ) );
		
		if value != ( self.mumbleid in acl.admingroup['add'] ):
			if value:
				acl.admingroup['add'].append( self.mumbleid );
			else:
				acl.admingroup['add'].remove( self.mumbleid );
		
		ctl.setACL(self.server.srvid, acl);
		return value;
	
	# Registration fetching
	def getRegistration( self ):
		"""Retrieve a user's registration from Murmur as a dict."""
		if not self._registration:
			self._registration = self.server.ctl.getRegistration( self.server.srvid, self.mumbleid );
		return self._registration;
	
	registration = property( getRegistration, doc=getRegistration.__doc__ );
	
	def getComment( self ):
		"""Retrieve a user's comment, if any."""
		if "comment" in self.registration:
			return self.registration["comment"];
		else:
			return None;
	
	comment = property( getComment, doc=getComment.__doc__ );
	
	def getHash( self ):
		if "hash" in self.registration:
			return self.registration["hash"];
		else:
			return None;
	
	hash = property( getHash, doc=getHash.__doc__ );
	
	# Texture handlers
	
	def getTexture( self ):
		"""Get the user texture as a PIL Image."""
		return self.server.ctl.getTexture(self.server.srvid, self.mumbleid);
	
	def setTexture( self, infile ):
		"""Read an image from the infile and install it as the user's texture."""
		self.server.ctl.setTexture(self.server.srvid, self.mumbleid, infile)
	
	texture = property( getTexture, setTexture, doc="Get the texture as a PIL Image or read from a file (pass the path)." );
	
	def hasTexture( self ):
		try:
			self.getTexture();
		except ValueError:
			return False;
		else:
			return True;
	
	def getTextureUrl( self ):
		""" Get a URL under which the texture can be retrieved. """
		from views				import showTexture
		from django.core.urlresolvers		import reverse
		return reverse( showTexture, kwargs={ 'server': self.server.id, 'userid': self.id } );
	
	textureUrl = property( getTextureUrl, doc=getTextureUrl.__doc__ );
	
	# Deletion handler
	
	@staticmethod
	def pre_delete_listener( **kwargs ):
		kwargs['instance'].unregister();
	
	def unregister( self ):
		"""Delete this user account from Murmur."""
		if self.getAdmin():
			self.setAdmin( False );
		self.server.ctl.unregisterPlayer(self.server.srvid, self.mumbleid)
	
	
	# "server" field protection
	
	def __setattr__( self, name, value ):
		if name == 'server':
			if self.id is not None and self.server != value:
				raise AttributeError( _( "This field must not be updated once the record has been saved." ) );
		
		models.Model.__setattr__( self, name, value );




signals.pre_delete.connect( Mumble.pre_delete_listener,     sender=Mumble     );
signals.pre_delete.connect( MumbleUser.pre_delete_listener, sender=MumbleUser );




