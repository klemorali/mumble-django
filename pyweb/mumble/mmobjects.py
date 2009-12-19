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
	
	def __init__( self, server, channelObj, parentChan = None ):
		self.server   = server;
		self.players  = list();
		self.subchans = list();
		self.linked   = list();
		
		self.channelObj = channelObj;
		self.chanid     = channelObj.id;
		self.linkedIDs  = channelObj.links;
		
		self.parent = parentChan;
		if self.parent is not None:
			self.parent.subchans.append( self );
		
		self._acl = None;
	
	# Lookup unknown attributes in self.channelObj to automatically include Murmur's fields
	def __getattr__( self, key ):
		if hasattr( self.channelObj, key ):
			return getattr( self.channelObj, key );
		else:
			raise AttributeError( "'%s' object has no attribute '%s'" % ( self.__class__.__name__, key ) );
	
	def parentChannels( self ):
		"""Return the names of this channel's parents in the channel tree."""
		if self.parent is None or self.parent.is_server or self.parent.chanid == 0:
			return [];
		return self.parent.parentChannels() + [self.parent.name];
	
	
	def getACL( self ):
		""" Retrieve the ACL for this channel. """
		if not self._acl:
			self._acl = mmACL( self, self.server.ctl.getACL( self.server.srvid, self.chanid ) );
		
		return self._acl;
	
	acl = property( getACL, doc=getACL.__doc__ );
	
	
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
	
	def asDict( self ):
		chandata = self.channelObj.__dict__.copy();
		chandata['players']  = [ pl.asDict() for pl in self.players  ];
		chandata['subchans'] = [ sc.asDict() for sc in self.subchans ];
		return chandata;




class mmPlayer( object ):
	"""Represents a Player in Murmur."""
	
	def __init__( self, srvInstance, playerObj, playerChan ):
		self.playerObj    = playerObj;
		
		self.onlinesince  = datetime.datetime.fromtimestamp( float( time() - playerObj.onlinesecs ) );
		self.channel      = playerChan;
		self.channel.players.append( self );
		
		if self.isAuthed:
			from models import Mumble, MumbleUser
			try:
				self.mumbleuser = MumbleUser.objects.get( mumbleid=self.userid, server=srvInstance );
			except MumbleUser.DoesNotExist:
				self.mumbleuser = None;
		else:
			self.mumbleuser = None;
	
	# Lookup unknown attributes in self.playerObj to automatically include Murmur's fields
	def __getattr__( self, key ):
		if hasattr( self.playerObj, key ):
			return getattr( self.playerObj, key );
		else:
			raise AttributeError( "'%s' object has no attribute '%s'" % ( self.__class__.__name__, key ) );
	
	def __str__( self ):
		return '<Player "%s" (%d, %d)>' % ( self.name, self.session, self.userid );
	
	isAuthed = property(
		lambda self: self.userid != -1,
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
		lambda self: "player_%d"%self.session,
		doc="A string ready to be used in an id property of an HTML tag."
		);
	
	def visit( self, callback, lvl = 0 ):
		""" Call callback on myself. """
		callback( self, lvl );
	
	def asDict( self ):
		pldata = self.playerObj.__dict__.copy();
		
		if self.mumbleuser:
			if self.mumbleuser.hasTexture():
				pldata['texture'] = self.mumbleuser.textureUrl;
		
		return pldata;



class mmACL:
	"""Represents an ACL for a certain channel."""
	
	def __init__( self, channel, aclObj ):
		self.channel = channel;
		self.acls, self.groups, self.inherit = aclObj;
		
		self.groups_dict = {};
		
		for group in self.groups:
			self.groups_dict[ group.name ] = group;
	
	def groupHasMember( self, name, userid ):
		""" Checks if the given userid is a member of the given group in this channel. """
		if name not in self.groups_dict:
			raise ReferenceError( "No such group '%s'" % name );
		
		return userid in self.groups_dict[name].add or userid in self.groups_dict[name].members;
	
	def groupAddMember( self, name, userid ):
		""" Make sure this userid is a member of the group in this channel (and subs). """
		if name not in self.groups_dict:
			raise ReferenceError( "No such group '%s'" % name );
		
		group = self.groups_dict[name];
		
		# if neither inherited nor to be added, add
		if userid not in group.members and userid not in group.add:
			group.add.append( userid );
		
		# if to be removed, unremove
		if userid in group.remove:
			group.remove.remove( userid );
	
	def groupRemoveMember( self, name, userid ):
		""" Make sure this userid is NOT a member of the group in this channel (and subs). """
		if name not in self.groups_dict:
			raise ReferenceError( "No such group '%s'" % name );
		
		group = self.groups_dict[name];
		
		# if added here, unadd
		if userid in group.add:
			group.add.remove( userid );
		# if member and not in remove, add to remove
		elif userid in group.members and userid not in group.remove:
			group.remove.append( userid );
	
	def save( self ):
		return self.channel.server.ctl.setACL(
			self.channel.server.srvid,
			self.channel.chanid,
			self.acls, self.groups, self.inherit
			);



