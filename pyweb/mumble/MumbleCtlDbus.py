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

from PIL	import Image
from struct	import pack, unpack
from zlib	import compress, decompress

from mctl	import MumbleCtlBase
from utils	import ObjectInfo

import dbus
from dbus.exceptions import DBusException


def MumbleCtlDbus( connstring ):
	meta = dbus.Interface( dbus.SystemBus().get_object( connstring, '/' ), 'net.sourceforge.mumble.Meta' );
	
	try:
		version = meta.getVersion();
	except DBusException:
		return MumbleCtlDbus_Legacy( connstring, meta );
	else:
		return MumbleCtlDbus_118( connstring, meta );


class MumbleCtlDbus_118(MumbleCtlBase):
	method = "DBus";
	
	def __init__( self, connstring, meta ):
		self.dbus_base = connstring;
		self.meta = meta;
	
	def _getDbusMeta( self ):
		return self.meta;
	
	def _getDbusServerObject( self, srvid):
		if srvid not in self.getBootedServers():
			raise SystemError, 'No murmur process with the given server ID (%d) is running and attached to system dbus under %s.' % ( srvid, self.meta );
		
		return dbus.Interface( dbus.SystemBus().get_object( self.dbus_base, '/%d' % srvid ), 'net.sourceforge.mumble.Murmur' );
	
	def getVersion( self ):
		return MumbleCtlDbus_118.convertDbusTypeToNative( self.meta.getVersion() )
	
	def getAllConf(self, srvid):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self.meta.getAllConf(dbus.Int32(srvid)))
	
	def setConf(self, srvid, key, value):
		self.meta.setConf(dbus.Int32( srvid ), key, value)
	
	def getDefaultConf(self):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self.meta.getDefaultConf())
	
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
	
	def registerPlayer(self, srvid, name, email, password):
		mumbleid = MumbleCtlDbus_118.convertDbusTypeToNative( self._getDbusServerObject(srvid).registerPlayer(name) );
		self.setRegistration( srvid, mumbleid, name, email, password );
		return mumbleid;
	
	def unregisterPlayer(self, srvid, mumbleid):
		self._getDbusServerObject(srvid).unregisterPlayer(dbus.Int32( mumbleid ))
	
	def getChannels(self, srvid):
		chans = MumbleCtlDbus_118.convertDbusTypeToNative(self._getDbusServerObject(srvid).getChannels())
		
		ret = {};
		
		for channel in chans:
			ret[ channel[0] ] = ObjectInfo(
				id        = channel[0],
				name      = channel[1],
				parent    = channel[2],
				links     = channel[3],
				);
		
		return ret;
	
	def getPlayers(self, srvid):
		players = MumbleCtlDbus_118.convertDbusTypeToNative(self._getDbusServerObject(srvid).getPlayers());
		
		ret = {};
		
		for playerObj in players:
			ret[ playerObj[0] ] = ObjectInfo(
				session      = playerObj[0],
				mute         = playerObj[1],
				deaf         = playerObj[2],
				suppress     = playerObj[3],
				selfMute     = playerObj[4],
				selfDeaf     = playerObj[5],
				channel      = playerObj[6],
				userid       = playerObj[7],
				name         = playerObj[8],
				onlinesecs   = playerObj[9],
				bytespersec  = playerObj[10]
				);
		
		return ret;
	
	def getRegisteredPlayers(self, srvid, filter = ''):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self._getDbusServerObject(srvid).getRegisteredPlayers( filter ) )
	
	def getACL(self, srvid, channelid):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self._getDbusServerObject(srvid).getACL(channelid))
	
	def setACL(self, srvid, acl):
		self._getDbusServerObject(srvid).setACL(*acl.pack())
	
	def getBootedServers(self):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self.meta.getBootedServers())
	
	def getAllServers(self):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self.meta.getAllServers())
	
	def setSuperUserPassword(self, srvid, value):
		self.meta.setSuperUserPassword(dbus.Int32(srvid), value)
	
	def getRegistration(self, srvid, mumbleid):
		user = MumbleCtlDbus_118.convertDbusTypeToNative(self._getDbusServerObject(srvid).getRegistration(dbus.Int32(mumbleid)))
		return {
			'name':  user[1],
			'email': user[2],
			};
	
	def setRegistration(self, srvid, mumbleid, name, email, password):
		return MumbleCtlDbus_118.convertDbusTypeToNative(
			self._getDbusServerObject(srvid).setRegistration(dbus.Int32(mumbleid), name, email, password)
			)
	
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
	
	def verifyPassword( self, srvid, username, password ):
		player = self.getRegisteredPlayers( srvid, username );
		if not player:
			return -2;
		
		ok = MumbleCtlDbus_118.convertDbusTypeToNative(
			self._getDbusServerObject(srvid).verifyPassword( dbus.Int32( player[0][0] ), password )
			);
		
		if ok:
			return player[0][0];
		else:
			return -1;
	
	@staticmethod
	def convertDbusTypeToNative(data):
		#i know dbus.* type is extends python native type.
		#but dbus.* type is not native type.  it's not good transparent for using Ice/Dbus.
		ret = None
		
		if isinstance(data, tuple) or type(data) is data.__class__ is dbus.Array or data.__class__ is dbus.Struct:
			ret = []
			for x in data:
				ret.append(MumbleCtlDbus_118.convertDbusTypeToNative(x))
		elif data.__class__ is dbus.Dictionary:
			ret = {}
			for x in data.items():
				ret[MumbleCtlDbus_118.convertDbusTypeToNative(x[0])] = MumbleCtlDbus_118.convertDbusTypeToNative(x[1])
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


class MumbleCtlDbus_Legacy( MumbleCtlDbus_118 ):
	def getVersion( self ):
		return ( 1, 1, 4, u"1.1.4" );
	
	def setRegistration(self, srvid, mumbleid, name, email, password):
		return MumbleCtlDbus_118.convertDbusTypeToNative(
			self._getDbusServerObject(srvid).updateRegistration( ( dbus.Int32(mumbleid), name, email, password ) )
			)




