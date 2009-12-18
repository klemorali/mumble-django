# -*- coding: utf-8 -*-

"""
 *  Copyright (C) 2009, withgod                   <withgod@sourceforge.net>
 *                      Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

from os.path		import join
from PIL		import Image
from struct		import pack, unpack
from zlib		import compress, decompress

from django.conf	import settings

from mctl		import MumbleCtlBase

import Ice


def protectDjangoErrPage( func ):
	""" Catch and reraise Ice exceptions to prevent the Django page from failing.
	
	    Since I need to "import Murmur", Django would try to read a murmur.py file
	    which doesn't exist, and thereby produce an IndexError exception. This method
	    erases the exception's traceback, preventing Django from trying to read any
	    non-existant files and borking.
	"""
	
	def protection_wrapper( *args, **kwargs ):
		try:
			return func( *args, **kwargs );
		except Ice.Exception, e:
			raise e;
	
	return protection_wrapper;



@protectDjangoErrPage
def MumbleCtlIce( connstring ):
	""" Choose the correct Ice handler to use (1.1.8 or 1.2.0), and make sure the
	    Murmur version matches the slice Version.
	"""
	
	version = settings.SLICE_VERSION;
	
	slice = settings.SLICE;
	if not slice:
		slice = join(
			settings.MUMBLE_DJANGO_ROOT, 'pyweb', 'mumble',
			'Murmur_%d-%d-%d.ice' % (version[0], version[1], version[2] )
			);
	
	Ice.loadSlice( slice )
	ice = Ice.initialize()
	import Murmur
	prx = ice.stringToProxy( connstring.encode("utf-8") )
	meta = Murmur.MetaPrx.checkedCast(prx)
	
	murmurversion = meta.getVersion();
	
	if murmurversion[0] != version[0] or murmurversion[1] != version[1] or murmurversion[2] != version[2]:
		raise TypeError(
			"Detected Murmur version %d.%d.%d, for which I am not configured." % ( murmurversion[0], murmurversion[1], murmurversion[2] )
			);
	
	if murmurversion[0] == murmurversion[1] == 1 and murmurversion[2] <= 8:
		return MumbleCtlIce_118( connstring, meta );
	elif murmurversion[0] == 1 and murmurversion[1] == 2 and murmurversion[2] == 0:
		return MumbleCtlIce_120( connstring, meta );



class MumbleCtlIce_118(MumbleCtlBase):
	method = "ICE";
	
	def __init__( self, connstring, meta ):
		self.proxy = connstring;
		self.meta  = meta;
	
	@protectDjangoErrPage
	def _getIceServerObject(self, srvid):
		return self.meta.getServer(srvid);
	
	@protectDjangoErrPage
	def getBootedServers(self):
		ret = []
		for x in self.meta.getBootedServers():
			ret.append(x.id())
		return ret
	
	@protectDjangoErrPage
	def getVersion( self ):
		return self.meta.getVersion();
	
	@protectDjangoErrPage
	def getAllServers(self):
		ret = []
		for x in self.meta.getAllServers():
			ret.append(x.id())
		return ret
	
	@protectDjangoErrPage
	def getRegisteredPlayers(self, srvid, filter = ''):
		users = self._getIceServerObject(srvid).getRegisteredPlayers( filter.encode( "UTF-8" ) )
		ret = []
		
		for user in users:
			ret.append([user.playerid, self.setUnicodeFlag(user.name), self.setUnicodeFlag(user.email), self.setUnicodeFlag(user.pw)])
		
		return ret
	
	@protectDjangoErrPage
	def getChannels(self, srvid):
		return self._getIceServerObject(srvid).getChannels();
	
	@protectDjangoErrPage
	def getPlayers(self, srvid):
		return self._getIceServerObject(srvid).getPlayers()
	
	@protectDjangoErrPage
	def getDefaultConf(self):
		return self.setUnicodeFlag(self.meta.getDefaultConf())
	
	@protectDjangoErrPage
	def getAllConf(self, srvid):
		return self.setUnicodeFlag(self._getIceServerObject(srvid).getAllConf())
	
	@protectDjangoErrPage
	def newServer(self):
		return self.meta.newServer().id()
	
	@protectDjangoErrPage
	def isBooted( self, srvid ):
		return bool( self._getIceServerObject(srvid).isRunning() );
	
	@protectDjangoErrPage
	def start( self, srvid ):
		self._getIceServerObject(srvid).start();
	
	@protectDjangoErrPage
	def stop( self, srvid ):
		self._getIceServerObject(srvid).stop();
	
	@protectDjangoErrPage
	def deleteServer( self, srvid ):
		if self._getIceServerObject(srvid).isRunning():
			self._getIceServerObject(srvid).stop()
		self._getIceServerObject(srvid).delete()
	
	@protectDjangoErrPage
	def setSuperUserPassword(self, srvid, value):
		self._getIceServerObject(srvid).setSuperuserPassword( value.encode( "UTF-8" ) )
	
	@protectDjangoErrPage
	def setConf(self, srvid, key, value):
		self._getIceServerObject(srvid).setConf( key, value.encode( "UTF-8" ) )
	
	@protectDjangoErrPage
	def registerPlayer(self, srvid, name, email, password):
		mumbleid = self._getIceServerObject(srvid).registerPlayer( name.encode( "UTF-8" ) )
		self.setRegistration( srvid, mumbleid, name, email, password );
		return mumbleid;
	
	@protectDjangoErrPage
	def unregisterPlayer(self, srvid, mumbleid):
		self._getIceServerObject(srvid).unregisterPlayer(mumbleid)
	
	@protectDjangoErrPage
	def getRegistration(self, srvid, mumbleid):
		user = self._getIceServerObject(srvid).getRegistration(mumbleid)
		return {
			'name':  user.name,
			'email': user.email,
			};
	
	@protectDjangoErrPage
	def setRegistration(self, srvid, mumbleid, name, email, password):
		user = self._getIceServerObject(srvid).getRegistration(mumbleid)
		user.name  = name.encode( "UTF-8" )
		user.email = email.encode( "UTF-8" )
		user.pw    = password.encode( "UTF-8" )
		# update*r*egistration r is lowercase...
		return self._getIceServerObject(srvid).updateregistration(user)
	
	@protectDjangoErrPage
	def getACL(self, srvid, channelid):
		import Murmur
		acls = self._getIceServerObject(srvid).getACL(channelid)
		ret = []
		for x in acls:
			if isinstance(x, list):
				tmp = []
				for y in x:
					if y.__class__ is Murmur.ACL:
						tmp.append([y.applyHere, y.applySubs, y.inherited, y.playerid, self.setUnicodeFlag(y.group), y.allow, y.deny])
					elif y.__class__ is Murmur.Group:
						tmp.append([self.setUnicodeFlag(y.name), y.inherited, y.inherit, y.inheritable, y.add, y.remove, y.members])
				
				ret.append(tmp)
			else:
				ret.append(x)
		
		return ret
	
	@protectDjangoErrPage
	def setACL(self, srvid, acl):
		import Murmur
		
		newacls   = [];
		newgroups = [];
		
		for curr_acl in acl.acls:
			new_acl = Murmur.ACL();
			new_acl.applyHere = curr_acl['applyHere'];
			new_acl.applySubs = curr_acl['applySubs'];
			new_acl.inherited = curr_acl['inherited'];
			new_acl.playerid  = curr_acl['playerid'];
			new_acl.group     = curr_acl['group'].encode( "UTF-8" );
			new_acl.allow     = curr_acl['allow'];
			new_acl.deny      = curr_acl['deny'];
			newacls.append( new_acl );
		
		for curr_group in acl.groups:
			new_group = Murmur.Group()
			new_group.name        = curr_group['name'].encode( "UTF-8" );
			new_group.inherited   = curr_group['inherited'];
			new_group.inherit     = curr_group['inherit'];
			new_group.inheritable = curr_group['inheritable'];
			new_group.add         = curr_group['add'];
			new_group.remove      = curr_group['remove'];
			new_group.members     = curr_group['members'];
			newgroups.append( new_group );
		
		self._getIceServerObject(srvid).setACL( acl.channelId, newacls, newgroups, acl.inherit );
	
	@protectDjangoErrPage
	def getTexture(self, srvid, mumbleid):
		texture = self._getIceServerObject(srvid).getTexture(mumbleid)
		if len(texture) == 0:
			raise ValueError( "No Texture has been set." );
		# this returns a list of bytes.
		decompressed = decompress( texture );
		# iterate over 4 byte chunks of the string
		imgdata = "";
		for idx in range( 0, len(decompressed), 4 ):
			# read 4 bytes = BGRA and convert to RGBA
			# manual wrote getTexture returns "Textures are stored as zlib compress()ed 600x60 32-bit RGBA data."
			# http://mumble.sourceforge.net/slice/Murmur/Server.html#getTexture
			# but return values BGRA X(
			bgra = unpack( "4B", decompressed[idx:idx+4] );
			imgdata += pack( "4B",  bgra[2], bgra[1], bgra[0], bgra[3] );
		
		# return an 600x60 RGBA image object created from the data
		return Image.fromstring( "RGBA", ( 600, 60 ), imgdata );
	
	@protectDjangoErrPage
	def setTexture(self, srvid, mumbleid, infile):
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
		self._getIceServerObject(srvid).setTexture(mumbleid, texture)
	
	@protectDjangoErrPage
	def verifyPassword(self, srvid, username, password):
		return self._getIceServerObject(srvid).verifyPassword(username, password);
	
	@staticmethod
	def setUnicodeFlag(data):
		ret = ''
		if isinstance(data, tuple) or isinstance(data, list) or isinstance(data, dict):
			ret = {}
			for key in data.keys():
				ret[MumbleCtlIce_118.setUnicodeFlag(key)] = MumbleCtlIce_118.setUnicodeFlag(data[key])
		else:
			ret = unicode(data, 'utf-8')
		
		return ret




class MumbleCtlIce_120(MumbleCtlIce_118):
	@protectDjangoErrPage
	def getRegisteredPlayers(self, srvid, filter = ''):
		users = self._getIceServerObject( srvid ).getRegisteredUsers( filter.encode( "UTF-8" ) )
		ret = []
		
		for id in users:
			ret.append( [ id, self.setUnicodeFlag( users[id] ) ] );
		
		return ret
	
	@protectDjangoErrPage
	def getPlayers(self, srvid):
		return self._getIceServerObject(srvid).getUsers();
	
	@protectDjangoErrPage
	def registerPlayer(self, srvid, name, email, password):
		# To get the real values of these ENUM entries, try
		# Murmur.UserInfo.UserX.value
		from Murmur import UserInfo
		user = {
			UserInfo.UserName:     name.encode( "UTF-8" ),
			UserInfo.UserEmail:    email.encode( "UTF-8" ),
			UserInfo.UserPassword: password.encode( "UTF-8" ),
			};
		return self._getIceServerObject(srvid).registerUser( user );
	
	@protectDjangoErrPage
	def unregisterPlayer(self, srvid, mumbleid):
		self._getIceServerObject(srvid).unregisterUser(mumbleid)
	
	@protectDjangoErrPage
	def getRegistration(self, srvid, mumbleid):
		from Murmur import UserInfo
		reg = self._getIceServerObject( srvid ).getRegistration( mumbleid )
		user = {};
		if UserInfo.UserName in reg:
			user['name'] = reg[UserInfo.UserName];
		if UserInfo.UserEmail in reg:
			user['email'] = reg[UserInfo.UserEmail];
		if UserInfo.UserComment in reg:
			user['comment'] = reg[UserInfo.UserComment];
		if UserInfo.UserHash in reg:
			user['hash'] = reg[UserInfo.UserHash];
		return user;
	
	@protectDjangoErrPage
	def setRegistration(self, srvid, mumbleid, name, email, password):
		from Murmur import UserInfo
		user = {
			UserInfo.UserName:     name.encode( "UTF-8" ),
			UserInfo.UserEmail:    email.encode( "UTF-8" ),
			UserInfo.UserPassword: password.encode( "UTF-8" ),
			};
		return self._getIceServerObject( srvid ).updateRegistration( mumbleid, user )
	
	@protectDjangoErrPage
	def getACL(self, srvid, channelid):
		import Murmur
		acls = self._getIceServerObject(srvid).getACL(channelid)
		ret = []
		for x in acls:
			if isinstance(x, list):
				tmp = []
				for y in x:
					if y.__class__ is Murmur.ACL:
						tmp.append([y.applyHere, y.applySubs, y.inherited, y.userid, self.setUnicodeFlag(y.group), y.allow, y.deny])
					elif y.__class__ is Murmur.Group:
						tmp.append([self.setUnicodeFlag(y.name), y.inherited, y.inherit, y.inheritable, y.add, y.remove, y.members])
				
				ret.append(tmp)
			else:
				ret.append(x)
		
		return ret
	
	@protectDjangoErrPage
	def setACL(self, srvid, acl):
		import Murmur
		
		newacls   = [];
		newgroups = [];
		
		for curr_acl in acl.acls:
			new_acl = Murmur.ACL();
			new_acl.applyHere = curr_acl['applyHere'];
			new_acl.applySubs = curr_acl['applySubs'];
			new_acl.inherited = curr_acl['inherited'];
			new_acl.userid    = curr_acl['playerid'];
			new_acl.group     = curr_acl['group'].encode( "UTF-8" );
			new_acl.allow     = curr_acl['allow'];
			new_acl.deny      = curr_acl['deny'];
			newacls.append( new_acl );
		
		for curr_group in acl.groups:
			new_group = Murmur.Group()
			new_group.name        = curr_group['name'].encode( "UTF-8" );
			new_group.inherited   = curr_group['inherited'];
			new_group.inherit     = curr_group['inherit'];
			new_group.inheritable = curr_group['inheritable'];
			new_group.add         = curr_group['add'];
			new_group.remove      = curr_group['remove'];
			new_group.members     = curr_group['members'];
			newgroups.append( new_group );
		
		self._getIceServerObject(srvid).setACL( acl.channelId, newacls, newgroups, acl.inherit );
	

