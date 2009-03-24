""" This file is part of the mumble-django application.
    
    Copyright (C) 2009, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 
    All rights reserved.
 
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
 
    - Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    - Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    - Neither the name of the Mumble Developers nor the names of its
      contributors may be used to endorse or promote products derived from this
      software without specific prior written permission.
 
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import models
import dbus
from django.db.models import signals

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
	bus = dbus.SystemBus();
	
	if "verbosity" in kwargs:
		v = kwargs['verbosity'];
	else:
		v = 1;
	
	if v > 1:
		print "Starting Mumble servers and players detection now.";
	
	dbusName = 'net.sourceforge.mumble.murmur';
	online = False;
	while not online:
		try:
			murmur = dbus.Interface( bus.get_object( dbusName, '/' ), 'net.sourceforge.mumble.Meta' );
		except dbus.exceptions.DBusException:
			if v:
				print "Unable to connect to DBus using name %s. Is Murmur even running!?" % dbusName;
			dbusName = raw_input( "DBus Service name (or empty to skip Servers/Players detection): " );
			if not dbusName:
				if v:
					print 'Be sure to run "python manage.py syncdb" with Murmur running before trying to use this app! Otherwise, existing Murmur servers won\'t be configurable!';
				return False;
		else:
			online = True;
			if v > 1:
				print "Successfully connected to Murmur via DBus (%s)." % dbusName;
	
	default = murmur.getDefaultConf();
	
	servIDs   = murmur.getAllServers();
	bootedIDs = murmur.getBootedServers();
	
	for id in servIDs:
		if v > 1:
			print "Checking Murmur instance with id %d." % id;
		# first check that the server has not yet been inserted into the DB
		try:
			instance = models.Mumble.objects.get( srvid=id );
		except models.Mumble.DoesNotExist:
			conf   = murmur.getAllConf( dbus.Int32( id ) );
			values = {
				"name":    find_in_dicts( "registerName",                conf, default, "noname" ),
				"srvid":   id,
				"dbus":    dbusName,
				"addr":    find_in_dicts( ( "registerHostame", "host" ), conf, default, "0.0.0.0" ),
				"port":    find_in_dicts( "port",                        conf, default ),
				"url":     find_in_dicts( "registerUrl",                 conf, default ),
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
			murmurinstance = dbus.Interface(
				bus.get_object( 'net.sourceforge.mumble.murmur', '/%d'%id ),
				'net.sourceforge.mumble.Murmur'
				);
			
			players = murmurinstance.getRegisteredPlayers('');
			
			for playerdata in players:
				if playerdata[0] == 0:
					continue;
				if v > 1:
					print "Checking Player with id %d and name '%s'." % playerdata[:2];
				try:
					models.MumbleUser.objects.get( mumbleid=playerdata[0] );
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
					playerinstance.save( dontConfigureMurmur=True );
				else:
					if v > 1:
						print "This player is already listed in the database.";
	
	if v > 1:
		print "Successfully finished Servers and Players detection.";
	return True;


signals.post_syncdb.connect( find_existing_instances, sender=models );





