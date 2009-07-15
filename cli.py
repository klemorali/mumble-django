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

import	locale
import	curses

from	django.db.models.fields.related		import ForeignKey

from	mumble.models				import *
from	mumble.forms				import *

locale.setlocale(locale.LC_ALL, '')


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



def oldmain():
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



class BaseWindow( object ):
	tabName = "tehBasez";
	
	def __init__( self, parentwin, mumble, pos_x, pos_y ):
		self.pos = ( pos_x, pos_y );
		self.win = parentwin.subwin( pos_y, pos_x );
		self.mm  = mumble;
		
		self.win.keypad(1);
	
	def draw( self ):
		self.win.addstr( 1, 1, self.tabName );
	
	def border( self ):
		self.win.border();
	
	def enter( self ):
		while( True ):
			key = self.win.getch();
			if key == curses.KEY_UP:
				return;


class FormEditor( object ):
	def __init__( self, win, form ):
		self.win      = win;
		self.form     = form;
	
	def draw( self ):
		curr_y = 1;
		
		for fname in self.form.fields:
			field = self.form.fields[fname];
			value = unicode( getattr( self.form.data, fname ) );
			
			self.win.addstr( curr_y, 1,  field.label.encode(locale.getpreferredencoding()) );
			self.win.addstr( curr_y, 30, value.encode(locale.getpreferredencoding()) );
			
			curr_y += 1;


class WndChannels( BaseWindow ):
	tabName = 'Channels';
	
	def printItem( self, item, level ):
		str = "";
		if item.is_server or item.is_channel:
			str = "%s (Channel)" % item.name;
		else:
			str = "%s (Player)" % item.name
		
		self.win.addstr( self.curr_y, 4*level+1, str.encode(locale.getpreferredencoding()) )
		self.curr_y += 1;
	
	def draw( self ):
		self.curr_y = 1;
		self.mm.rootchan.visit( self.printItem );


class WndSettings( BaseWindow, FormEditor ):
	tabName = 'Server settings';
	
	def __init__( self, parentwin, mumble, pos_x, pos_y ):
		BaseWindow.__init__( self, parentwin, mumble, pos_x, pos_y );
		FormEditor.__init__( self, self.win,  MumbleAdminForm( mumble ) );
	
	def draw( self ):
		FormEditor.draw( self );


class WndUsers( BaseWindow ):
	tabName = 'Registered users';


class MumbleForm( object ):
	def __init__( self, parentwin, mumble, pos_x, pos_y ):
		self.pos = ( pos_x, pos_y );
		self.win = parentwin.subwin( pos_y, pos_x );
		self.mm  = mumble;
		
		self.win.keypad(1);
		
		self.windows = (
			WndChannels( self.win, mumble, pos_x + 2, pos_y + 2 ),
			WndSettings( self.win, mumble, pos_x + 2, pos_y + 2 ),
			WndUsers(    self.win, mumble, pos_x + 2, pos_y + 2 ),
			);
		
		self.curridx = 0;
		self.currmax = len( self.windows ) - 1;
	
	currwin = property( lambda self: self.windows[self.curridx], None );
	
	def mvwin( self, pos_x, pos_y ):
		self.win.mvwin( pos_y, pos_x );
	
	def mvdefault( self ):
		self.win.mvwin( self.pos[1], self.pos[0] );
	
	def draw( self ):
		self.win.addstr( 0, 0, self.mm.name.encode(locale.getpreferredencoding()) );
	
	def drawTabs( self ):
		first = True;
		for subwin in self.windows:
			flags = 0;
			if subwin is self.currwin: flags |= curses.A_STANDOUT;
			
			if first:
				self.win.addstr( 1, 2, "%-20s" % subwin.tabName, flags );
				first = False;
			else:
				self.win.addstr( "%-20s" % subwin.tabName, flags );
	
	def enter( self ):
		self.drawTabs();
		self.currwin.draw();
		self.currwin.border();
		
		while( True ):
			key = self.win.getch();
			
			if key == curses.KEY_LEFT and self.curridx > 0:
				self.curridx -= 1;
			
			elif key == curses.KEY_RIGHT and self.curridx < self.currmax:
				self.curridx += 1;
			
			elif key in ( ord('q'), ord('Q'), curses.KEY_UP ):
				return;
			
			elif key in ( curses.KEY_ENTER, curses.KEY_DOWN, ord('\n') ):
				self.currwin.enter();
			
			self.win.clear();
			self.draw();
			self.drawTabs();
			self.currwin.draw();
			self.currwin.border();
			self.win.refresh();
			



def main( stdscr ):
	first_y = 3;
	curr_y  = first_y;
	
	mumbles = list();
	
	for mm in Mumble.objects.all().order_by( "name", "id" ):
		mwin = MumbleForm( stdscr, mm, pos_x=5, pos_y=curr_y );
		mumbles.append( mwin );
		mwin.draw();
		curr_y += 1;
	
	selectedIdx = 0;
	selectedMax = len(mumbles) - 1;
	
	while( True ):
		selectedObj = mumbles[selectedIdx];
		
		# Draw selection marker
		stdscr.addstr( first_y + selectedIdx, 3, '*' );
		stdscr.refresh();
		
		key = stdscr.getch();
		if key == curses.KEY_UP:
			stdscr.addstr( first_y + selectedIdx, 3, ' ' );
			selectedIdx -= 1;
		
		elif key == curses.KEY_DOWN:
			stdscr.addstr( first_y + selectedIdx, 3, ' ' );
			selectedIdx += 1;
		
		elif key in ( curses.KEY_RIGHT, curses.KEY_ENTER, ord('\n') ):
			stdscr.clear();
			selectedObj.mvwin( 5, first_y );
			selectedObj.draw();
			stdscr.refresh();
			
			selectedObj.enter();
			
			stdscr.clear();
			selectedObj.mvdefault();
			for mwin in mumbles:
				mwin.draw();
		
		elif key in ( ord('q'), ord('Q') ):
			return;
		
		if   selectedIdx < 0:           selectedIdx = 0;
		elif selectedIdx > selectedMax: selectedIdx = selectedMax;
	




if __name__ == '__main__':
	#parser = OptionParser();
	#parser.add_option( "-v", "--verbose", help="verbose output messages",   default=False, action="store_true" );
	#parser.add_option( "-n", "--num",     help="size of the Matrix",	 default=4,     type = 'int'	 );
	#parser.add_option( "-s", "--sure",    help="don't prompt if num >= 10", default=False, action="store_true" );
	#options, args = parser.parse_args();
	
	curses.wrapper( main );













