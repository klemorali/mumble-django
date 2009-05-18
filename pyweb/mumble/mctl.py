# -*- coding: utf-8 -*-
# mumble-django contributed by withgod@sourceforge.net

import dbus

#zope.interface is good but don't standard interface library
#abc is better but 2.6 higher.
#import abc

#from django.conf import settings

class MumbleCtlBase ():
	''' abstract Ctrol Object '''

	def setConf(self, srvid, key, value):
		pass

	def getValue(self, srvid, key):
		pass

	def newServer(self):
		pass

	def setSuperUserPassword(self, srvid, value):
		pass

	def start(self, srvid):
		pass

	def stop(self, srvid):
		pass

	def isBooted(self, srvid):
		pass

	def deleteServer(self, srvid):
		pass

	def getUsers(self, srvid):
		pass

	def getPlayers(self, srvid):
		pass

	def getChannels(self, srvid):
		pass

	def registerPlayer(self, srvid, name):
		pass

	def setRegistration(self, mumbleid, name, email, password):
		pass

	def getBootedServers(self):
		pass

	def getACL(self, srvid, identifier):
		pass

	@staticmethod
	def newInstance():
		# if dbus
		#if settings.DAOTYPE == 'dbus':
		ret = MumbleCtlDbus()
		#else:
		#	ret = MumbleCtlIce()
		return ret

class MumbleCtlDbus(MumbleCtlBase):
	meta   = None
	dbus_base='net.sourceforge.mumble.murmur'

	def __init__(self):
		# Prior to saving the model, connect to murmur via dbus and update its settings.
		self.meta = self._getDbusMeta();

	def _getDbusMeta( self ):
		return dbus.Interface( dbus.SystemBus().get_object( self.dbus_base, '/' ), 'net.sourceforge.mumble.Meta' );
	
	def _getDbusServerObject( self, srvid):
		"Connects to DBus and returns an mmServer object representing this Murmur instance."

		if srvid not in self.getBootedServers():
			raise Exception, 'No murmur process with the given server ID (%d) is running and attached to system dbus under %s.' % ( srvid, self.meta );

		return dbus.Interface( dbus.SystemBus().get_object( self.dbus_base, '/%d' % srvid ), 'net.sourceforge.mumble.Murmur' );

	def setConf(self, srvid, key, value):
		srvid = dbus.Int32( srvid )
		self.meta.setConf(srvid, key, value)

	def deleteServer( self, srvid ):
		srvid = dbus.Int32( srvid );
		if self.meta.isBooted( srvid ):
			self.meta.stop( srvid );
		self.meta.deleteServer( srvid );

	def registerPlayer(self, name):
		pass

	def getChannels(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getChannels())

	def getPlayers(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getPlayers())

	def getACL(self, srvid, identifier):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).getACL(identifier))

	def getBootedServers(self):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getBootedServers())

	def setSuperUserPassword(self, srvid, value):
		self.meta.setSuperUserPassword(dbus.Int32(srvid), value)

	def registerPlayer(self, srvid, name):
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).registerPlayer(srvid, name))

	@staticmethod
	def converDbusTypeToNative(data):
		#i know dbus.* type is extends python native type.
		#but dbus.* type is not native type.  it's not good transparent for using Ice/Dbus.
		ret = None

		if isinstance(data, tuple) or type(data) is data.__class__ is dbus.Array or data.__class__ is dbus.Struct :
			ret = []
			for x in data:
				ret.append(MumbleCtlDbus.converDbusTypeToNative(x))
		else:
			if data.__class__ is dbus.Boolean:
				ret = bool(data)
			elif data.__class__  is dbus.String:
				ret = str(data)
			elif data.__class__  is dbus.Int32 or data.__class__ is dbus.UInt32:
				ret = int(data)
		return ret

if __name__ == "__main__":
	print "--- test start"
	#ctl = MumbleCtlBase.newInstance()
	ctl = MumbleCtlDbus()
	print ctl
	print ctl.meta
	print "booted server", ctl.getBootedServers()
	print "chans"
	print ctl.getChannels(1)
	print "users"
	print ctl.getPlayers(1)
	print "getACL", ctl.getACL(1, 0)
	print ctl.getACL(1, 0)[0].__class__ is dbus.Array
	
	print "--- test end"

