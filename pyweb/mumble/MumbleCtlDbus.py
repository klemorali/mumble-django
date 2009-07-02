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

from mctl import MumbleCtlBase

import dbus
class MumbleCtlDbus(MumbleCtlBase):
	method = "DBus";
	
	def __init__( self, connstring ):
		# Prior to saving the model, connect to murmur via dbus and update its settings.
		self.dbus_base = connstring;
		self.meta = self._getDbusMeta();
	
	def _getDbusMeta( self ):
		return dbus.Interface( dbus.SystemBus().get_object( self.dbus_base, '/' ), 'net.sourceforge.mumble.Meta' );
	
	def _getDbusServerObject( self, srvid):
		"Connects to DBus and returns an mmServer object representing this Murmur instance."
		
		if srvid not in self.getBootedServers():
			raise Exception, 'No murmur process with the given server ID (%d) is running and attached to system dbus under %s.' % ( srvid, self.meta );
		
		return dbus.Interface( dbus.SystemBus().get_object( self.dbus_base, '/%d' % srvid ), 'net.sourceforge.mumble.Murmur' );
	
	def getVersion( self ):
		return MumbleCtlDbus.converDbusTypeToNative( self.meta.getVersion() )
	
	def getAllConf(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getAllConf(dbus.Int32(srvid)))

	def setConf(self, srvid, key, value):
		self.meta.setConf(dbus.Int32( srvid ), key, value)

	def getDefaultConf(self):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getDefaultConf())
	
	def start( self, srvid ):
		self.meta.start( srvid );

	def stop( self, srvid ):
		self.meta.stop( srvid );

	def isBooted( self, srvid ):
		return bool( self.meta.isBooted( srvid ) );
	
	def deleteServer( self, srvid ):
		srvid = dbus.Int32( srvid )
		if self.meta.isBooted( srvid ):
			self.meta.stop( srvid )

		self.meta.deleteServer( srvid )

	def newServer(self):
		return self.meta.newServer()

	def registerPlayer(self, srvid, name):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).registerPlayer(name))

	def unregisterPlayer(self, srvid, mumbleid):
		self._getDbusServerObject(srvid).unregisterPlayer(dbus.Int32( mumbleid ))

	def getChannels(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getChannels())

	def getPlayers(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getPlayers())

	def getRegisteredPlayers(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getRegisteredPlayers(''))

	def getACL(self, srvid, identifier):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getACL(identifier))

	def setACL(self, srvid, acl):
		self._getDbusServerObject(srvid).setACL(*acl.pack())

	def getBootedServers(self):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getBootedServers())

	def getAllServers(self):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getAllServers())

	def setSuperUserPassword(self, srvid, value):
		self.meta.setSuperUserPassword(dbus.Int32(srvid), value)

	def setRegistration(self, srvid, mumbleid, name, email, password):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).setRegistration(dbus.Int32(mumbleid), name, email, password))
		#return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).setRegistration(dbus.Int32(mumbleid), dbus.String(name), dbus.String(email), dbus.String(password)))

	def getTexture(self, srvid, mumbleid):
		texture = self._getDbusServerObject(srvid).getTexture(dbus.Int32(mumbleid));
		
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
		self._getDbusServerObject(srvid).setTexture(dbus.Int32( mumbleid ), texture)

	@staticmethod
	def converDbusTypeToNative(data):
		#i know dbus.* type is extends python native type.
		#but dbus.* type is not native type.  it's not good transparent for using Ice/Dbus.
		ret = None

		if isinstance(data, tuple) or type(data) is data.__class__ is dbus.Array or data.__class__ is dbus.Struct:
			ret = []
			for x in data:
				ret.append(MumbleCtlDbus.converDbusTypeToNative(x))
		elif data.__class__ is dbus.Dictionary:
			ret = {}
			for x in data.items():
				ret[MumbleCtlDbus.converDbusTypeToNative(x[0])] = MumbleCtlDbus.converDbusTypeToNative(x[1])
		else:
			if data.__class__ is dbus.Boolean:
				ret = bool(data)
			elif data.__class__  is dbus.String:
				ret = unicode(data)
			elif data.__class__  is dbus.Int32 or data.__class__ is dbus.UInt32:
				ret = int(data)
			elif data.__class__ is dbus.Byte:
				ret = byte(data)
		return ret
