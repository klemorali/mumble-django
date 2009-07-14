#!/usr/bin/python
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

# Set this to the same path you used in settings.py, or None for auto-detection.
MUMBLE_DJANGO_ROOT = None;

### DO NOT CHANGE ANYTHING BELOW THIS LINE ###

import os, sys
from os.path import join, dirname, abspath, exists

# Path auto-detection
if not MUMBLE_DJANGO_ROOT or not exists( MUMBLE_DJANGO_ROOT ):
	MUMBLE_DJANGO_ROOT = dirname(abspath(__file__));

# environment variables
sys.path.append( MUMBLE_DJANGO_ROOT )
sys.path.append( join( MUMBLE_DJANGO_ROOT, 'pyweb' ) )
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyweb.settings'


# If you get an error about Python not being able to write to the Python
# egg cache, the egg cache path might be set awkwardly. This should not
# happen under normal circumstances, but every now and then, it does.
# Uncomment this line to point the egg cache to /tmp.
#os.environ['PYTHON_EGG_CACHE'] = '/tmp/pyeggs'

from django.db.models.fields.related   import ForeignKey
from mumble.models import *

def getNum( prompt, **kwargs ):
	id = None;
	while type(id) != int:
		print
		try:
			id = raw_input( "%s >>> " % prompt ).strip();
			if id == 'q':
				return None;
			elif id in kwargs:
				return kwargs[id];
			id = int( id );
		except Exception, instance:
			print "Error reading input. Did you type a number?";
			print instance;
	return id;

def util_editModel( model, blacklist = None ):
	while True:
		print "Current settings"
		print "================"
		for field in model._meta.fields:
			if blacklist and field.name in blacklist:
				continue;
			
			print "#%-5d %-30s %s" % ( model._meta.fields.index( field ), field.verbose_name, getattr( model, field.name ) );
		
		print "================"
		print "Enter the index of the parameter you would like to change,"
		print "or q to return."
		
		idx = getNum( "Index" );
		if idx is None:
			save = raw_input( "save? Y/n >>> " );
			if not save or save.lower() == 'y':
				print "saving changes.";
				model.save();
			else:
				print "NOT saving changes."
			return;
		
		field = model._meta.fields[idx];
		if blacklist and field.name in blacklist:
			print "This field can not be changed.";
		elif isinstance( field, ForeignKey ):
			print "This is a ForeignKey.";
			print field.rel.to.objects.all();
		else:
			value = None;
			while value is None:
				print
				try:
					value = field.to_python( raw_input( "%s >>> " % field.name ).strip() );
				except Exception, instance:
					print instance;
			setattr( model, field.name, value );


def act_serverDetails( server ):
	"View or edit server settings."
	util_editModel( server, ( "id", "sslcrt", "sslkey" ) );


def act_registeredUsers( server ):
	"View or edit user registrations."
	
	mumbleusers_list = server.mumbleuser_set.all();
	
	print "Currently registered accounts";
	print "=============================";
	
	for mu in mumbleusers_list:
		if mu.owner is not None:
			print "#%-5d %-20s Owner: %-20s Admin: %s" % ( mu.id, mu.name, mu.owner.username, mu.getAdmin() );
		else:
			print "#%-5d %-20s" % ( mu.id, mu.name );
	
	print "=============================";
	print "Enter the ID of the account you would like to change, n to create a new one, or q to return."
	
	while True:
		idx = getNum( "ID", n=-1 );
		if idx is None:
			return;
		
		if idx == -1:
			mu = MumbleUser();
			mu.server = server;
		else:
			mu = mumbleusers_list.get( id=idx );
		
		util_editModel( mu, ( "id", "mumbleid", "server" ) );


def act_listChannels( server ):
	"Display a channel tree."
	
	def printItem( item, level ):
		print "%s%s" % ( "   "*level, item );
	
	server.rootchan.visit( printItem );


def act_chanDetails( server ):
	"Display detailed information about one specific channel."
	print "Please choose the channel by entering the according ID (the number in parentheses)."
	act_listChannels( server );
	
	id = getNum( "ID" );
	if id is None: return;
	
	print "Channel name: %s" % server.channels[id].name
	print "Channel ID:   %d" % server.channels[id].chanid
	print "Users online: %d" % len( server.channels[id].players )
	print "Linked chans: %d" % len( server.channels[id].linked  )


def cli_chooseServer():
	mumble_all = Mumble.objects.all().order_by( 'name', 'id' );
	
	print "Please choose a Server instance by typing the corresponding ID.\n";
	
	for mm in mumble_all:
		print "#%d\t%s" % ( mm.id, mm.name );
	print "n: Create new instance";
	print "q: Exit";
	
	id = getNum( "ID", n = -1 );
	
	if id is None:
		return;
	elif id == -1:
		return Mumble();
	
	return Mumble.objects.get( id=id );


def cli_chooseAction( server ):
	actions = {
		"LISTCHAN":   act_listChannels,
		"CHANINFO":   act_chanDetails,
		"EDITSERVER": act_serverDetails,
		"EDITUSERS":  act_registeredUsers,
		};
	
	while True:
		print "What do you want to do?"
		
		keys = actions.keys();
		
		for act in keys:
			print "#%-5d %-20s %s" % ( keys.index(act), act, actions[act].__doc__ );
		print "q: Return to server selection";
		
		idx = getNum( "Index" );
		if idx is None:
			return;
		
		# call action function
		func = actions[ keys[idx] ]
		func( server );
		print



def main():
	print
	
	while True:
		mumble = cli_chooseServer();
		if mumble is None:
			print "Bye.";
			return;
		
		print "Selected %s." % mumble;
		print
		
		cli_chooseAction( mumble );
		print




if __name__ == '__main__':
	#parser = OptionParser();
	#parser.add_option( "-v", "--verbose", help="verbose output messages",   default=False, action="store_true" );
	#parser.add_option( "-n", "--num",     help="size of the Matrix",	 default=4,     type = 'int'	 );
	#parser.add_option( "-s", "--sure",    help="don't prompt if num >= 10", default=False, action="store_true" );
	#options, args = parser.parse_args();
	
	main();













