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

from PIL    import Image
from struct import pack, unpack
from zlib   import compress, decompress

from django.conf import settings

from mctl import MumbleCtlBase

import Ice

class MumbleCtlIce(MumbleCtlBase):
	method = "ICE";
	
	def __init__( self, connstring ):
		self.proxy = connstring;
		self.meta  = self._getIceMeta()

	def _getIceMeta(self):
		Ice.loadSlice(settings.SLICE)
		ice = Ice.initialize()
		import Murmur
		prx = ice.stringToProxy(self.proxy)
		return Murmur.MetaPrx.checkedCast(prx)

	def _getIceServerObject(self, srvid):
		return self.meta.getServer(srvid);

	def getBootedServers(self):
		ret = []
		for x in self.meta.getBootedServers():
			ret.append(x.id())
		return ret

	def getAllServers(self):
		ret = []
		for x in self.meta.getAllServers():
			ret.append(x.id())
		return ret

	def getRegisteredPlayers(self, srvid):
		users = self._getIceServerObject(srvid).getRegisteredPlayers('')
		ret = []

		for user in users:
			ret.append([user.playerid, MumbleCtlIce.setUnicodeFlag(user.name), MumbleCtlIce.setUnicodeFlag(user.email), MumbleCtlIce.setUnicodeFlag(user.pw)])

		return ret

	def getChannels(self, srvid):
		chans = self._getIceServerObject(srvid).getChannels()
		ret = []

		for x in chans:
			chan = chans[x]
			ret.append([chan.id, MumbleCtlIce.setUnicodeFlag(chan.name), chan.parent, chan.links])

		return ret

	def getPlayers(self, srvid):
		users = self._getIceServerObject(srvid).getPlayers()
		ret = []

		for x in users:
			user = users[x]
			ret.append([user.session, user.mute, user.deaf, user.suppressed, user.selfMute, user.selfDeaf, user.channel, user.playerid, MumbleCtlIce.setUnicodeFlag(user.name), user.onlinesecs, user.bytespersec])

		return ret

	def getACL(self, srvid, identifier):
		import Murmur
		acls = self._getIceServerObject(srvid).getACL(identifier)
		ret = []
		for x in acls:
			if isinstance(x, list):
				tmp = []
				for y in x:
					if y.__class__ is Murmur.ACL:
						tmp.append([y.applyHere, y.applySubs, y.inherited, y.playerid, MumbleCtlIce.setUnicodeFlag(y.group), y.allow, y.deny])
					elif y.__class__ is Murmur.Group:
						tmp.append([MumbleCtlIce.setUnicodeFlag(y.name), y.inherited, y.inherit, y.inheritable, y.add, y.remove, y.members])

				ret.append(tmp)
			else:
				ret.append(x)

		return ret

	def getDefaultConf(self):
		return MumbleCtlIce.setUnicodeFlag(self.meta.getDefaultConf())

	def getAllConf(self, srvid):
		return MumbleCtlIce.setUnicodeFlag(self._getIceServerObject(srvid).getAllConf())

	def newServer(self):
		return self.meta.newServer().id()

	def deleteServer( self, srvid ):
		if self._getIceServerObject(srvid).isRunning():
			self._getIceServerObject(srvid).stop()
		self._getIceServerObject(srvid).delete()

	def setSuperUserPassword(self, srvid, value):
		self.meta.setSuperUserPassword(srvid, value)

	def setConf(self, srvid, key, value):
		value = value.encode("utf-8")
		#print "%s server %s=%s (%s/%s)" % (srvid, key, value, type(key), type(value))
		self._getIceServerObject(srvid).setConf(key, value)

	def registerPlayer(self, srvid, name):
		return self._getIceServerObject(srvid).registerPlayer(name)

	def unregisterPlayer(self, srvid, mumbleid):
		self._getIceServerObject(srvid).unregisterPlayer(mumbleid)

	def setRegistration(self, srvid, mumbleid, name, email, password):
		user = self._getIceServerObject(srvid).getRegistration(mumbleid)
		user.name  = name
		user.email = email
		user.pw    = password
		#print user
		# update*r*egistration r is lowercase...
		return self._getIceServerObject(srvid).updateregistration(user)

	def setACL(self, srvid, acl):
		'''
		print "xxxx"
		print srvid
		print acl
		print "--"
		print acl.pack()
		print "xxxx"
		'''
		import Murmur
		tmp     = acl.pack()
		id      = tmp[0]
		_acls   = tmp[1]
		acls    = []
		_groups = tmp[2]
		groups  = []
		inherit = tmp[3]

		for x in _acls:
			acl = Murmur.ACL()
			acl.applyHere = x[0]
			acl.applySubs = x[1]
			acl.inherited = x[2]
			acl.playerid  = x[3]
			acl.group     = x[4]
			acl.allow     = x[5]
			acl.deny      = x[6]
			acls.append(acl)

		for x in _groups:
			group = Murmur.Group()
			group.name        = x[0]
			group.inherited   = x[1]
			group.inherit     = x[2]
			group.inheritable = x[3]
			group.add         = x[4]
			group.remove      = x[5]
			group.members     = x[6]
			groups.append(group)

		self._getIceServerObject(srvid).setACL(id, acls, groups, inherit)

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
		return Image.fromstring( "RGBA", ( 600, 60 ), imgdata);

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

	@staticmethod
	def setUnicodeFlag(data):
		ret = ''
		if isinstance(data, tuple) or isinstance(data, list) or isinstance(data, dict):
			ret = {}
			for key in data.keys():
				ret[MumbleCtlIce.setUnicodeFlag(key)] = MumbleCtlIce.setUnicodeFlag(data[key])
		else:
			ret = unicode(data, 'utf-8')

		return ret

