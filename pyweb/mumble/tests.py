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

import os

from django.test		import TestCase
from django.test.simple 	import run_tests as django_run_tests
from django.conf		import settings

from models			import *
from utils			import ObjectInfo
from murmurenvutils		import get_available_versions, run_callback


class InstancesHandling( TestCase ):
	""" Tests creation, editing and removing of vserver instances. """
	
	def setUp( self ):
		# Make sure we always start with a FRESH murmur instance, checking for left-over instances
		# and deleting them before creating ours.
		try:
			self.murmur = Mumble.objects.get( addr="0.0.0.0", port=31337 );
		except Mumble.DoesNotExist:
			pass
		else:
			self.murmur.delete();
		finally:
			self.murmur = Mumble( name="#unit testing instance#", addr="0.0.0.0", port=31337 );
			self.murmur.save();
	
	def testDefaultConf( self ):
		conf = self.murmur.ctl.getAllConf( self.murmur.srvid );
		
		self.assert_( type(conf) == dict );
		self.assert_( "host"             in conf );
		self.assert_( "port"             in conf );
		self.assert_( "certificate"      in conf );
		self.assert_( "key"              in conf );
		self.assert_( "registerhostname" in conf );
		self.assert_( "registername"     in conf );
		self.assert_( "channelname"      in conf );
		self.assert_( "username"         in conf );
		self.assert_( "obfuscate"        in conf );
		self.assert_( "defaultchannel"   in conf );
	
	def testAddrPortUnique( self ):
		try:
			duplicate = Mumble( name="#another unit testing instance#", addr="0.0.0.0", port=31337 );
			if duplicate.ctl.method == "ICE":
				import Murmur
				self.assertRaises( Murmur.ServerFailureException, duplicate.save );
			else:
				from sqlite3 import IntegrityError
				self.assertRaises( IntegrityError, duplicate.save );
		finally:
			# make sure the duplicate is removed
			duplicate.ctl.deleteServer( duplicate.srvid );
	
	def tearDown( self ):
		self.murmur.delete();


class DataReading( TestCase ):
	""" Tests reading data from murmur using the low-level CTL methods. """
	
	def setUp( self ):
		# BIG FAT WARNING: This sucks ass, because it assumes the tester has a
		# Murmur database like the one I have.
		# I definitely need to prepare Murmur somehow before running these tests.
		# Just don't yet know how.
		self.murmur = Mumble.objects.get(id=1);
	
	
	def testCtlGetChannels( self ):
		""" Test getChannels() """
		
		channels = self.murmur.ctl.getChannels( self.murmur.srvid );
		
		if self.murmur.ctl.method == "ICE":
			import Murmur
			self.assertEquals( type( channels[0] ), Murmur.Channel );
		else:
			self.assertEquals( type( channels[0] ), ObjectInfo );
		
		self.assert_( hasattr( channels[0], "id"     ) );
		self.assert_( hasattr( channels[0], "name"   ) );
		self.assert_( hasattr( channels[0], "parent" ) );
		self.assert_( hasattr( channels[0], "links"  ) );
	
	
	def testCtlGetPlayers( self ):
		""" Test getPlayers() """
		
		players = self.murmur.ctl.getPlayers( self.murmur.srvid );
		
		self.assert_( len(players) > 0 );
		
		self.assertEquals( type(players), dict );
		
		for plidx in players:
			player = players[plidx];
			
			if self.murmur.ctl.method == "ICE" and self.murmur.version[:2] == ( 1, 2 ):
				import Murmur
				self.assertEquals( type( player ), Murmur.User );
			else:
				self.assertEquals( type( player ), ObjectInfo );
			
			self.assert_( hasattr( player, "session" ) );
			self.assert_( hasattr( player, "mute" ) );
			self.assert_( hasattr( player, "deaf" ) );
			self.assert_( hasattr( player, "selfMute" ) );
			self.assert_( hasattr( player, "selfDeaf" ) );
			self.assert_( hasattr( player, "channel" ) );
			self.assert_( hasattr( player, "userid" ) );
			self.assert_( hasattr( player, "name" ) );
			self.assert_( hasattr( player, "onlinesecs" ) );
			self.assert_( hasattr( player, "bytespersec" ) );
	
	
	def testCtlGetRegisteredPlayers( self ):
		""" Test getRegistredPlayers() and getRegistration() """
		
		players = self.murmur.ctl.getRegisteredPlayers( self.murmur.srvid );
		
		self.assert_( len(players) > 0 );
		
		self.assertEquals( type(players), dict );
		
		for plidx in players:
			player = players[plidx];
			
			self.assertEquals( type( player ), ObjectInfo );
			
			self.assert_( hasattr( player, "userid" ) );
			self.assert_( hasattr( player, "name"   ) );
			self.assert_( hasattr( player, "email"  ) );
			self.assert_( hasattr( player, "pw"     ) );
			
			# compare with getRegistration result
			reg = self.murmur.ctl.getRegistration( self.murmur.srvid, player.userid );
			
			self.assertEquals( type( reg ), ObjectInfo );
			
			self.assert_( hasattr( reg, "userid" ) );
			self.assert_( hasattr( reg, "name"   ) );
			self.assert_( hasattr( reg, "email"  ) );
			self.assert_( hasattr( reg, "pw"     ) );
			
			self.assertEquals( player.userid, reg.userid );
			self.assertEquals( player.name,   reg.name   );
			self.assertEquals( player.email,  reg.email  );
			self.assertEquals( player.pw,     reg.pw     );
	
	
	def testCtlGetAcl( self ):
		""" Test getACL() for the root channel """
		
		acls, groups, inherit = self.murmur.ctl.getACL( self.murmur.srvid, 0 );
		
		for rule in acls:
			if self.murmur.ctl.method == "ICE" and self.murmur.version[:2] == ( 1, 2 ):
				import Murmur
				self.assertEquals( type( rule ), Murmur.ACL );
			else:
				self.assertEquals( type( rule ), ObjectInfo );
			
			self.assert_( hasattr( rule, "applyHere" ) );
			self.assert_( hasattr( rule, "applySubs" ) );
			self.assert_( hasattr( rule, "inherited" ) );
			self.assert_( hasattr( rule, "userid"    ) );
			self.assert_( hasattr( rule, "group"     ) );
			self.assert_( hasattr( rule, "allow"     ) );
			self.assert_( hasattr( rule, "deny"      ) );
		
		for grp in groups:
			if self.murmur.ctl.method == "ICE" and self.murmur.version[:2] == ( 1, 2 ):
				import Murmur
				self.assertEquals( type( grp ), Murmur.Group );
			else:
				self.assertEquals( type( grp ), ObjectInfo );
			
			self.assert_( hasattr( grp,  "name"        ) );
			self.assert_( hasattr( grp,  "inherited"   ) );
			self.assert_( hasattr( grp,  "inherit"     ) );
			self.assert_( hasattr( grp,  "inheritable" ) );
			self.assert_( hasattr( grp,  "add"         ) );
			self.assert_( hasattr( grp,  "remove"      ) );
			self.assert_( hasattr( grp,  "members"     ) );


def run_tests( test_labels, verbosity=1, interactive=True, extra_tests=[] ):
	""" Run the Django built in testing framework, but before testing the mumble
	    app, allow Murmur to be set up correctly.
	"""
	
	if not test_labels:
		test_labels = [ appname.split('.')[-1] for appname in settings.INSTALLED_APPS ];
	
	# No need to sync any murmur servers for the other apps
	os.environ['MURMUR_CONNSTR'] = '';
	
	# The easy way: mumble is not being tested.
	if "mumble" not in test_labels:
		return django_run_tests( test_labels, verbosity, interactive, extra_tests );
	
	# First run everything apart from mumble. mumble will be tested separately, so Murmur
	# can be set up properly first.
	
	test_labels.remove( "mumble" );
	failed_tests = django_run_tests( test_labels, verbosity, interactive, extra_tests );
	
	failed_tests += run_mumble_tests( verbosity, interactive );
	
	return failed_tests;


def run_mumble_tests( verbosity=1, interactive=True ):
	
	connstrings = {
		'DBus': 'net.sourceforge.mumble.murmur',
		'Ice':  'Meta:tcp -h 127.0.0.1 -p 6502',
		};
	
	failed_tests = 0;
	
	def django_run_tests_wrapper( process ):
		return django_run_tests( ('mumble',), verbosity, interactive, [] ), False;
	
	for version in get_available_versions():
		for method in connstrings:
			print "Testing mumble %s via %s" % ( version, method );
			os.environ['MURMUR_CONNSTR'] = connstrings[method];
			settings.DEFAULT_CONN        = connstrings[method];
			failed_tests += run_callback( version, django_run_tests_wrapper );
	
	return failed_tests;

