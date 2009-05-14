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

import dbus

import datetime
from time import time


# base = ice.stringToProxy( "Meta:tcp -h 127.0.0.1 -p 6502" );
# srv = Murmur.ServerPrx.checkedCast( base );
# met = Murmur.MetaPrx.checkedCast( base );

class mmServer( object ):
	# channels    = dict();
	# players     = dict();
	# id          = int();
	# rootName    = str();
	
	def __init__( self, serverID, serverObj, rootName = '' ):
		self.dbusObj  = serverObj;
		self.channels = dict();
		self.players  = dict();
		self.id       = serverID;
		self.rootName = rootName;
		
		links         = dict();
		
		for theChan in serverObj.getChannels():
			# Channels - Fields: 0 = ID, 1 = Name, 2 = Parent-ID, 3 = Links
			
			if( theChan[2] == -1 ):
				# No parent
				self.channels[theChan[0]] = mmChannel( theChan );
			else:
				self.channels[theChan[0]] = mmChannel( theChan, self.channels[theChan[2]] );
			
			self.channels[theChan[0]].serverId = self.id;
			
			# process links - if the linked channels are known, link; else save their ids to link later
			for linked in theChan[3]:
				if linked in self.channels:
					self.channels[theChan[0]].linked.append( self.channels[linked] );
				else:
					if linked not in links:
						links[linked] = list();
					links[linked].append( self.channels[theChan[0]] );
					#print "Saving link: %s <- %s" % ( linked, self.channels[theChan[0]] );
			
			# check if earlier round trips saved channel ids to be linked to the current channel
			if theChan[0] in links:
				for targetChan in links[theChan[0]]:
					targetChan.linked.append( self.channels[theChan[0]] );
		
		if self.rootName:
			self.channels[0].name = self.rootName;
		
		for thePlayer in serverObj.getPlayers():
			# Players - Fields: 0 = UserID, 6 = ChannelID
			self.players[ thePlayer[0] ] = mmPlayer( thePlayer, self.channels[ thePlayer[6] ] );
			
	
	playerCount = property(
		lambda self: len( self.players ),
		None
		);
	
	def is_server( self ):
		return True;
	def is_channel( self ):
		return False;
	def is_player( self ):
		return False;
	
	def __str__( self ):
		return '<Server "%s" (%d)>' % ( self.rootName, self.id );
	
	def visit( self, callback, lvl = 0 ):
		if not callable( callback ):
			raise Exception, "a callback should be callable...";
		
		# call callback first on myself, then visit my root chan
		callback( self, lvl );
		self.channels[0].visit( callback, lvl + 1 );


class mmChannel( object ):
	# channels  = list();
	# subchans  = list();
	# chanid    = int();
	# name      = str();
	# parent    = mmChannel();
	# linked    = list();
	# linkedIDs = list();
	
	def __init__( self, channelObj, parentChan = None ):
		self.players  = list();
		self.subchans = list();
		self.linked   = list();
		
		(self.chanid, self.name, parent, self.linkedIDs ) = channelObj;
		
		self.parent = parentChan;
		if self.parent is not None:
			self.parent.subchans.append( self );
			self.serverId = self.parent.serverId;
	
	def parentChannels( self ):
		if self.parent is None or self.parent.is_server() or self.parent.chanid == 0:
			return [];
		return self.parent.parentChannels() + [self.parent.name];
	
	def is_server( self ):
		return False;
	def is_channel( self ):
		return True;
	def is_player( self ):
		return False;
	
	playerCount = property(
		lambda self: len( self.players ) + sum( [ chan.playerCount for chan in self.subchans ] ),
		None
		);
	id = property( lambda self: "channel_%d"%self.chanid, None );
	
	def __str__( self ):
		return '<Channel "%s" (%d)>' % ( self.name, self.chanid );
	
	def visit( self, callback, lvl = 0 ):
		# call callback on myself, then visit my subchans, then my players
		callback( self, lvl );
		for sc in self.subchans:
			sc.visit( callback, lvl + 1 );
		for pl in self.players:
			pl.visit( callback, lvl + 1 );



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
	
	def __init__( self, playerObj, playerChan ):
		( self.userid, self.muted, self.deafened, self.suppressed, self.selfmuted, self.selfdeafened, chanID, self.dbaseid, self.name, onlinetime, self.bytesPerSec ) = playerObj;
		self.onlinesince = datetime.datetime.fromtimestamp( float( time() - onlinetime ) );
		self.channel = playerChan;
		self.channel.players.append( self );
		
		if self.isAuthed():
			from models import Mumble, MumbleUser
			srvInstance     = Mumble.objects.get( srvid=self.channel.serverId );
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
	
	def is_server( self ):
		return False;
	def is_channel( self ):
		return False;
	def is_player( self ):
		return True;
	
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



