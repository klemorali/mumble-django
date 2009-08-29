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

import models
from django.db.models		import signals

from mctl			import *

def find_in_dicts( keys, conf, default, valueIfNotFound=None ):
	if not isinstance( keys, tuple ):
		keys = ( keys, );

	for keyword in keys:
		if keyword in conf:
			return conf[keyword];

	for keyword in keys:
		keyword = keyword.lower();
		if keyword in default:
			return default[keyword];

	return valueIfNotFound;


def find_existing_instances( **kwargs ):
	if "verbosity" in kwargs:
		v = kwargs['verbosity'];
	else:
		v = 1;
	
	if v > 1:
		print "Starting Mumble servers and players detection now.";
	
	triedEnviron = False;
	online = False;
	while not online:
		if not triedEnviron and 'MURMUR_CONNSTR' in os.environ:
			dbusName = os.environ['MURMUR_CONNSTR'];
			triedEnviron = True;
		else:
			print "--- Murmur connection info ---"
			print "  1) DBus -- net.sourceforge.mumble.murmur"
			print "  2) ICE  -- Meta:tcp -h 127.0.0.1 -p 6502"
			print "Enter 1 or 2 for the defaults above, nothing to skip Server detection,"
			print "and if the defaults do not fit your needs, enter the correct string."
			print "Whether to use DBus or ICE will be detected automatically from the"
			print "string's format."
			print
			
			dbusName = raw_input( "Service string: " ).strip();
		
		if not dbusName:
			if v:
				print 'Be sure to run "python manage.py syncdb" with Murmur running before trying to use this app! Otherwise, existing Murmur servers won\'t be configurable!';
			return False;
		elif dbusName == "1":
			dbusName = "net.sourceforge.mumble.murmur";
		elif dbusName == "2":
			dbusName = "Meta:tcp -h 127.0.0.1 -p 6502";
		
		try:
			ctl = MumbleCtlBase.newInstance( dbusName );
		except Exception, instance:
			if v:
				print "Unable to connect using name %s. The error was:" % dbusName;
				print instance;
				print
		else:
			online = True;
			if v > 1:
				print "Successfully connected to Murmur via connection string %s, using %s." % ( dbusName, ctl.method );
	
	default = ctl.getDefaultConf();
	
	servIDs   = ctl.getAllServers();
	bootedIDs = ctl.getBootedServers();
	
	for id in servIDs:
		if v > 1:
			print "Checking Murmur instance with id %d." % id;
		# first check that the server has not yet been inserted into the DB
		try:
			instance = models.Mumble.objects.get( dbus=dbusName, srvid=id );
		except models.Mumble.DoesNotExist:
			conf   = ctl.getAllConf(id);
			
			servername = find_in_dicts( "registername",                conf, default, "noname" );
			if not servername:
				# RegistrationName was found in the dicts, but is an empty string
				servername = "noname";
			
			values = {
				"name":    servername,
				"srvid":   id,
				"dbus":    dbusName,
				"addr":    find_in_dicts( ( "registerhostame", "host" ), conf, default, "0.0.0.0" ),
				"port":    find_in_dicts( "port",                        conf, default ),
				"url":     find_in_dicts( "registerurl",                 conf, default ),
				"motd":    find_in_dicts( "welcometext",                 conf, default ),
				"passwd":  find_in_dicts( "password",                    conf, default ),
				"supw":    '',
				"users":   find_in_dicts( "users",                       conf, default ),
				"bwidth":  find_in_dicts( "bandwidth",                   conf, default ),
				"sslcrt":  find_in_dicts( "certificate",                 conf, default ),
				"sslkey":  find_in_dicts( "key",                         conf, default ),
				"booted":  ( id in bootedIDs ),
				}
			
			if values['addr'].find( ':' ) != -1:
				# The addr is a hostname which actually contains a port number, but we already got that from
				# the port field, so we can simply drop it.
				values['addr'] = values['addr'].split(':')[0];
			
			if v:
				print 'Found new Murmur "%s" running on %s:%s.' % ( values['name'], values['addr'], values['port'] );
			
			# now create a model for the record set.
			instance = models.Mumble( **values );
			instance.save( dontConfigureMurmur=True );
		else:
			if v > 1:
				print "This instance is already listed in the database.";
		
		# Now search for players on this server that have not yet been registered
		if v > 1:
			print "Looking for registered Players on Server id %d." % id;
		if id in bootedIDs:
			players = ctl.getRegisteredPlayers(id);
			
			for playerdata in players:
				if playerdata[0] == 0:
					continue;
				if v > 1:
					print "Checking Player with id %d and name '%s'." % ( int(playerdata[0]), playerdata[1] );
				try:
					models.MumbleUser.objects.get( server=instance, mumbleid=playerdata[0] );
				except models.MumbleUser.DoesNotExist:
					if v:
						print 'Found new Player "%s".' % playerdata[1];
					playerinstance = models.MumbleUser(
						mumbleid = playerdata[0],
						name     = playerdata[1],
						password = '',
						server   = instance,
						owner    = None
						);
					playerinstance.isAdmin = playerinstance.getAdmin();
					playerinstance.save( dontConfigureMurmur=True );
				else:
					if v > 1:
						print "This player is already listed in the database.";
	
	if v > 1:
		print "Successfully finished Servers and Players detection.";
	return True;


signals.post_syncdb.connect( find_existing_instances, sender=models );





