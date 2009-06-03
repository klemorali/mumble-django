# -*- coding: utf-8 -*-
# mumble-django contributed by withgod@sourceforge.net


#zope.interface is good but don't standard interface library
#abc is better but 2.6 higher.
#import abc

from django.conf import settings

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
		if settings.DAOTYPE == 'dbus':
			from MumbleCtlDbus import MumbleCtlDbus
			return MumbleCtlDbus()
		else:
			from MumbleCtlIce import MumbleCtlIce
			return MumbleCtlIce()

if __name__ == "__main__":
	import sys
	from MumbleCtlIce import MumbleCtlIce
	from MumbleCtlDbus import MumbleCtlDbus
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

