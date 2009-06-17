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
from time       import time
from os.path    import join

from django.utils.http import urlquote


class mmChannel( object ):
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
		
		(self.chanid, self.name, parent, self.linkedIDs ) = channelObj;
		
		self.parent = parentChan;
		if self.parent is not None:
			self.parent.subchans.append( self );
	
	
	def parentChannels( self ):
		if self.parent is None or self.parent.is_server or self.parent.chanid == 0:
			return [];
		return self.parent.parentChannels() + [self.parent.name];
	
	
	is_server  = False;
	is_channel = True;
	is_player  = False;
	
	
	playerCount = property(
		lambda self: len( self.players ) + sum( [ chan.playerCount for chan in self.subchans ] ),
		None
		);
	
	id   = property( lambda self: "channel_%d"%self.chanid, None );
	
	show = property( lambda self: self.parent is None or self.parent.chanid == 0 or self.playerCount > 0, None );
	
	def __str__( self ):
		return '<Channel "%s" (%d)>' % ( self.name, self.chanid );
	
	def visit( self, callback, lvl = 0 ):
		# call callback on myself, then visit my subchans, then my players
		callback( self, lvl );
		for sc in self.subchans:
			sc.visit( callback, lvl + 1 );
		for pl in self.players:
			pl.visit( callback, lvl + 1 );
	
	
	def getURL( self, forUser = None ):
		# mumble://username@host:port/parentchans/self.name
		userstr = "";
		
		if forUser is not None:
			userstr = "%s@" % forUser.name;
		
		# create list of all my parents and myself
		chanlist = self.parentChannels() + [self.name];
		# urlencode channel names
		chanlist = [ urlquote( chan ) for chan in chanlist ];
		# create a path by joining the channel names
		chanpath = join( *chanlist );
		
		return "mumble://%s%s:%d/%s" % ( userstr, self.server.addr, self.server.port, chanpath );
	
	url = property( getURL, None );



class mmPlayer( object ):
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
		
		if self.isAuthed():
			from models import Mumble, MumbleUser
			try:
				self.mumbleuser = MumbleUser.objects.get( mumbleid=self.dbaseid, server=srvInstance );
			except MumbleUser.DoesNotExist:
				self.mumbleuser = None;
		else:
			self.mumbleuser = None;
	
	def __str__( self ):
		return '<Player "%s" (%d, %d)>' % ( self.name, self.userid, self.dbaseid );
	
	def isAuthed( self ):
		return self.dbaseid != -1;
	
	isAdmin = property(
		lambda self: self.mumbleuser and self.mumbleuser.getAdmin(),
		None
		);
	
	is_server  = False;
	is_channel = False;
	is_player  = True;
	
	# kept for compatibility to mmChannel (useful for traversal funcs)
	playerCount = property( lambda self: -1, None );
	id = property( lambda self: "player_%d"%self.userid, None );
	
	def visit( self, callback, lvl = 0 ):
		callback( self, lvl );



class mmACL:
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
		return (
			self.channelId,
			[( acl['applyHere'], acl['applySubs'], acl['inherited'], acl['playerid'], acl['group'], acl['allow'], acl['deny'] ) for acl in self.acls ],
			[( group['name'], group['inherited'], group['inherit'], group['inheritable'], group['add'], group['remove'], group['members'] ) for group in self.groups ],
			self.inherit
			);



