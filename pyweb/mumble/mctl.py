# -*- coding: utf-8 -*-
# mumble-django contributed by withgod@sourceforge.net

import dbus

#zope.interface is good but don't standard interface library
#abc is better but 2.6 higher.
#import abc

#from django.conf import settings

class MumbleCtlBase ():
	''' abstract Ctrol Object '''

	def getAllConf(self, srvid):
		pass

	def setConf(self, srvid, key, value):
		pass

	def getDefaultConf(self):
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

	def getRegisteredPlayers(self, srvid):
		pass

	def getChannels(self, srvid):
		pass

	def registerPlayer(self, srvid, name):
		pass

	def setRegistration(self, srvid, mumbleid, name, email, password):
		pass

	def unregisterPlayer(self, srvid, mumbleid):
		pass

	def getBootedServers(self):
		pass

	def getAllServers(self):
		pass

	def getACL(self, srvid, identifier):
		pass

	def setACL(self, srvid, acl):
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

	def getAllConf(self, srvid):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getAllConf(dbus.Int32(srvid)))

	def setConf(self, srvid, key, value):
		self.meta.setConf(dbus.Int32( srvid ), key, value)

	def getDefaultConf(self):
		return MumbleCtlDbus.converDbusTypeToNative(self.meta.getDefaultConf())

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
		return MumbleCtlDbus.converDbusTypeToNative(self._getDbusServerObject(srvid).setRegistration(dbus.Int32(mumbleid), dbus.String(name), dbus.String(email), dbus.String(password)))

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
	print "getAllServers()"
	print ctl.getAllServers()
	print "getDefaultConf()"
	print ctl.getDefaultConf()
	print "getAllConf(1)"
	print ctl.getAllConf(1)
	
	print "--- test end"

