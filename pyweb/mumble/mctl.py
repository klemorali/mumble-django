# -*- coding: utf-8 -*-
# mumble-django contributed by withgod@sourceforge.net


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
		#ret = MumbleCtlDbus()
		ret = MumbleCtlIce()
		#else:
		#	ret = MumbleCtlIce()
		return ret

import Ice
class MumbleCtlIce(MumbleCtlBase):
	proxy = 'Meta:tcp -h 127.0.0.1 -p 6502'
	slice = '/usr/share/slice/Murmur.ice'
	meta = None

	def __init__(self):
		self.meta = self._getIceMeta()

	def _getIceMeta(self):
		Ice.loadSlice(self.slice)
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
			ret.append([user.playerid, unicode(user.name), unicode(user.email), unicode(user.pw)])

		return ret

	def getChannels(self, srvid):
		chans = self._getIceServerObject(srvid).getChannels()
		ret = []

		for x in chans:
			chan = chans[x]
			ret.append([chan.id, unicode(chan.name), chan.parent, chan.links])

		return ret

	def getPlayers(self, srvid):
		users = self._getIceServerObject(srvid).getPlayers()
		ret = []

		for x in users:
			user = users[x]
			ret.append([user.session, user.mute, user.deaf, user.suppressed, user.selfMute, user.selfDeaf, user.channel, user.playerid, unicode(user.name), user.onlinesecs, user.bytespersec])

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
						tmp.append([y.applyHere, y.applySubs, y.inherited, y.playerid, unicode(y.group), y.allow, y.deny])
					elif y.__class__ is Murmur.Group:
						tmp.append([unicode(y.name), y.inherited, y.inherit, y.inheritable, y.add, y.remove, y.members])

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
		#print "%s server %s/%s" % (srvid, key, value)
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

	@staticmethod
	def setUnicodeFlag(data):
		ret = {}
		for key in data.keys():
			ret[unicode(key)] = unicode(data[key])
		return ret

import dbus
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
	import sys
	x = int(sys.argv[1])
	dbusCtl = MumbleCtlDbus()
	iceCtl = MumbleCtlIce()
	'''
	print "--- Dbus test start"
	#ctl = MumbleCtlBase.newInstance()
	print dbusCtl
	print dbusCtl.meta
	print "booted server", dbusCtl.getBootedServers()
	print "chans"
	print dbusCtl.getChannels(x)
	print "users"
	print dbusCtl.getPlayers(x)
	print "getACL", dbusCtl.getACL(x, 0)
	print "getAllServers()"
	print dbusCtl.getAllServers()
	print "getDefaultConf()"
	print dbusCtl.getDefaultConf()
	print "getAllConf(x)"
	print dbusCtl.getAllConf(x)
	print "--Dbus end--"
	print "--- Ice test start"
	print iceCtl
	print iceCtl.meta
	print "booted server", iceCtl.getBootedServers()
	print "chans"
	print iceCtl.getChannels(x)
	print "users"
	print iceCtl.getPlayers(x)
	print "getACL", iceCtl.getACL(x, 0)
	print "getAllServers()"
	print iceCtl.getAllServers()
	print "getDefaultConf()"
	print iceCtl.getDefaultConf()
	print "getAllConf(x)"
	print iceCtl.getAllConf(x)
	print "--- Ice test end"
	'''

	print "equal test ---"
	print "getBootedServers			[%s]" % (dbusCtl.getBootedServers() == iceCtl.getBootedServers())
	print "getChannels				[%s]" % (dbusCtl.getChannels(x) == iceCtl.getChannels(x))
	print "getPlayers				[%s]" % (dbusCtl.getPlayers(x) == iceCtl.getPlayers(x))
	print "getACL(x, 0)				[%s]" % (dbusCtl.getACL(x, 0) == iceCtl.getACL(x, 0))
	print "getAllServers			[%s]" % (dbusCtl.getAllServers() == iceCtl.getAllServers())
	print "getDefaultConf			[%s]" % (dbusCtl.getDefaultConf() == iceCtl.getDefaultConf())
	print "getAllConf(x)			[%s]" % (dbusCtl.getAllConf(x) == iceCtl.getAllConf(x))
	print "getRegisteredPlayers(x)	[%s]" % (dbusCtl.getRegisteredPlayers(x) == iceCtl.getRegisteredPlayers(x))


	#print iceCtl.getRegisteredPlayers(x)
	#print iceCtl.getACL(x, 0)

