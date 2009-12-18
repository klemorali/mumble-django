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

import mctl

import datetime
from time			import time
from os.path			import join

from django.utils.http		import urlquote
from django.conf		import settings

def cmp_names( a, b ):
	return cmp( a.name, b.name );


class mmChannel( object ):
	"""Represents a channel in Murmur."""
	
	# channels  = list();
	# subchans  = list();
	# chanid    = int();
	# name      = str();
	# parent    = mmChannel();
	# linked    = list();
	# linkedIDs = list();
	
	def __init__( self, server, channelObj, parentChan = None ):
		self.server   = server;
		self.players  = list();
		self.subchans = list();
		self.linked   = list();
		
		self.chanid    = channelObj.id;
		self.name      = channelObj.name;
		parent         = channelObj.parent;
		self.linkedIDs = channelObj.links;
		
		if hasattr( channelObj, "description" ):
			self.description = channelObj.description;
		else:
			self.description = "";
		
		if hasattr( channelObj, "temporary" ):
			self.temporary = channelObj.temporary;
		else:
			self.temporary = False;
		
		if hasattr( channelObj, "position" ):
			self.position = channelObj.position;
		else:
			# None would be better imho, but Murmur reports 0 for unknown too.
			self.position = 0;
		
		self.parent = parentChan;
		if self.parent is not None:
			self.parent.subchans.append( self );
	
	
	def parentChannels( self ):
		"""Return the names of this channel's parents in the channel tree."""
		if self.parent is None or self.parent.is_server or self.parent.chanid == 0:
			return [];
		return self.parent.parentChannels() + [self.parent.name];
	
	
	is_server  = False;
	is_channel = True;
	is_player  = False;
	
	
	playerCount = property(
		lambda self: len( self.players ) + sum( [ chan.playerCount for chan in self.subchans ] ),
		doc="The number of players in this channel."
		);
	
	id   = property(
		lambda self: "channel_%d"%self.chanid,
		doc="A string ready to be used in an id property of an HTML tag."
		);
	
	top_or_not_empty = property(
		lambda self: self.parent is None or self.parent.chanid == 0 or self.playerCount > 0,
		doc="True if this channel needs to be shown because it is root, a child of root, or has players."
		);
	
	show =  property( lambda self: settings.SHOW_EMPTY_SUBCHANS or self.top_or_not_empty );
	
	def __str__( self ):
		return '<Channel "%s" (%d)>' % ( self.name, self.chanid );
	
	def sort( self ):
		"""Sort my subchannels and players, and then iterate over them and sort them recursively."""
		self.subchans.sort( cmp_names );
		self.players.sort( cmp_names );
		for sc in self.subchans:
			sc.sort();
	
	def visit( self, callback, lvl = 0 ):
		"""Call callback on myself, then visit my subchans, then my players."""
		callback( self, lvl );
		for sc in self.subchans:
			sc.visit( callback, lvl + 1 );
		for pl in self.players:
			pl.visit( callback, lvl + 1 );
	
	
	def getURL( self, forUser = None ):
		"""
		Create an URL to connect to this channel. The URL is of the form
		mumble://username@host:port/parentchans/self.name
		"""
		userstr = "";
		
		if forUser is not None:
			userstr = "%s@" % forUser.name;
		
		versionstr = "version=%d.%d.%d" % tuple(self.server.version[0:3]);
		
		# create list of all my parents and myself
		chanlist = self.parentChannels() + [self.name];
		# urlencode channel names
		chanlist = [ urlquote( chan ) for chan in chanlist ];
		# create a path by joining the channel names
		chanpath = join( *chanlist );
		
		if self.server.port != settings.MUMBLE_DEFAULT_PORT:
			return "mumble://%s%s:%d/%s?%s" % ( userstr, self.server.addr, self.server.port, chanpath, versionstr );
		
		return "mumble://%s%s/%s?%s" % ( userstr, self.server.addr, chanpath, versionstr );
	
	connecturl = property( getURL, doc="A convenience wrapper for getURL." );
	
	def setDefault( self ):
		"Make this the server's default channel."
		self.server.defchan = self.chanid;
		self.server.save();
	
	is_default = property(
		lambda self: self.server.defchan == self.chanid,
		doc="True if this channel is the server's default channel."
		);
	
	def as_dict( self ):
		if self.parent:
			parentid = self.parent.chanid;
		else:
			parentid = None;
		
		return { 'chanid':      self.chanid,
			 'description': self.description,
			 'temporary':   self.temporary,
			 'position':    self.position,
			 'linked':      [],
			 'linkedIDs':   [],
			 'name':        self.name,
			 'parent':      parentid,
			 'players':     [ pl.as_dict() for pl in self.players  ],
			 'subchans':    [ sc.as_dict() for sc in self.subchans ]
			};




class mmPlayer( object ):
	"""Represents a Player in Murmur."""
	
	# muted        = bool;
	# deafened     = bool;
	# suppressed   = bool;
	# selfmuted    = bool;
	# selfdeafened = bool;
	
	# channel      = mmChannel();
	# dbaseid      = int();
	# userid       = int();
	# name         = str();
	# onlinesince  = time();
	# bytesPerSec  = int();
	
	# mumbleuser   = models.MumbleUser();
	
	def __init__( self, srvInstance, playerObj, playerChan ):
		( self.userid, self.muted, self.deafened, self.suppressed, self.selfmuted, self.selfdeafened, chanID, self.dbaseid, self.name, onlinetime, self.bytesPerSec ) = playerObj;
		self.onlinesince = datetime.datetime.fromtimestamp( float( time() - onlinetime ) );
		self.channel = playerChan;
		self.channel.players.append( self );
		
		if self.isAuthed:
			from models import Mumble, MumbleUser
			try:
				self.mumbleuser = MumbleUser.objects.get( mumbleid=self.dbaseid, server=srvInstance );
			except MumbleUser.DoesNotExist:
				self.mumbleuser = None;
		else:
			self.mumbleuser = None;
	
	def __str__( self ):
		return '<Player "%s" (%d, %d)>' % ( self.name, self.userid, self.dbaseid );
	
	isAuthed = property(
		lambda self: self.dbaseid != -1,
		doc="True if this player is authenticated (+A)."
		);
	
	isAdmin = property(
		lambda self: self.mumbleuser and self.mumbleuser.getAdmin(),
		doc="True if this player is in the Admin group in the ACL."
		);
	
	is_server  = False;
	is_channel = False;
	is_player  = True;
	
	# kept for compatibility to mmChannel (useful for traversal funcs)
	playerCount = property( lambda self: -1, doc="Exists only for compatibility to mmChannel." );
	
	id = property(
		lambda self: "player_%d"%self.userid,
		doc="A string ready to be used in an id property of an HTML tag."
		);
	
	def visit( self, callback, lvl = 0 ):
		""" Call callback on myself. """
		callback( self, lvl );
	
	def as_dict( self ):
		comment = None;
		texture = None;
		if self.mumbleuser:
			comment = self.mumbleuser.comment;
			if self.mumbleuser.hasTexture():
				texture = self.mumbleuser.textureUrl;
		
		return { 'bytesPerSec':  self.bytesPerSec,
			 'dbaseid':      self.dbaseid,
			 'deafened':     self.deafened,
			 'muted':        self.muted,
			 'name':         self.name,
			 'onlinesince':  self.onlinesince,
			 'selfdeafened': self.selfdeafened,
			 'selfmuted':    self.selfmuted,
			 'suppressed':   self.suppressed,
			 'userid':       self.userid,
			 'comment':      comment,
			 'texture':      texture,
			};



class mmACL:
	"""Represents an ACL for a certain channel."""
	
	def __init__( self, channelId, aclObj ):
		aclsrc, groupsrc, inherit = aclObj;
		
		self.channelId = channelId;
		
		self.acls = [];
		for line in aclsrc:
			acl = {};
			acl['applyHere'], acl['applySubs'], acl['inherited'], acl['playerid'], acl['group'], acl['allow'], acl['deny'] = line;
			self.acls.append( acl );
		
		self.groups = [];
		for line in groupsrc:
			group = {};
			group['name'], group['inherited'], group['inherit'], group['inheritable'], group['add'], group['remove'], group['members'] = line;
			self.groups.append( group );
			if group['name'] == "admin":
				self.admingroup = group;
		
		self.inherit = inherit;
	
	def pack( self ):
		""" Pack the information in this ACL up in a way that it can be passed to DBus. """
		return (
			self.channelId,
			[( acl['applyHere'], acl['applySubs'], acl['inherited'], acl['playerid'], acl['group'], acl['allow'], acl['deny'] ) for acl in self.acls ],
			[( group['name'], group['inherited'], group['inherit'], group['inheritable'], group['add'], group['remove'], group['members'] ) for group in self.groups ],
			self.inherit
			);



