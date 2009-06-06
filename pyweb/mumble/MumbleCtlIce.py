# -*- coding: utf-8 -*-
# mumble-django contributed by withgod@sourceforge.net

from PIL    import Image
from struct import pack, unpack
from zlib   import compress, decompress

from mctl import MumbleCtlBase

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



	def getTexture(self, srvid, mumbleid):
		print self._getIceServerObject(srvid).getTexture(mumbleid)
		#return Image.fromstring( "RGBA", ( 600, 60 ), self._getIceServerObject(srvid).getTexture(mumbleid));

	@staticmethod
	def setUnicodeFlag(data):
		ret = {}
		for key in data.keys():
			ret[unicode(key)] = unicode(data[key])
		return ret

