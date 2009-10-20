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
from	curses.textpad				import Textbox

from	django.core.exceptions			import ValidationError
from	django.db.models.fields.related		import ForeignKey
from	django.db				import models

from	mumble.models				import *
from	mumble.forms				import *

locale.setlocale(locale.LC_ALL, '')


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


class WndChannels( BaseWindow ):
	tabName = 'Channels';
	
	def printItem( self, item, level ):
		namestr = "";
		if item.is_server or item.is_channel:
			namestr = "%s (Channel)" % item.name;
		else:
			namestr = "%s (Player)" % item.name
		
		self.win.addstr( self.curr_y, 4*level+1, namestr.encode(locale.getpreferredencoding()) )
		self.curr_y += 1;
	
	def draw( self ):
		self.curr_y = 1;
		self.mm.rootchan.visit( self.printItem );


class WndSettings( BaseWindow ):
	tabName = 'Server settings';
	
	blacklist = ( 'id', 'sslkey', 'sslcrt' );
	
	def __init__( self, parentwin, mumble, pos_x, pos_y ):
		BaseWindow.__init__( self, parentwin, mumble, pos_x, pos_y );
		self.form     = MumbleAdminForm( instance=mumble );
		
		self.editors  = {};
		self.fields   = [ mf for mf in mumble._meta.fields if mf.name not in self.blacklist ];
	
	def getFieldHeight( self, field ):
		if isinstance( field, models.TextField ):
			return 10;
		return 1;
	
	def getFieldYPos( self, field ):
		ypos = 3;
		for curr_field in self.fields:
			if curr_field is field:
				return ypos;
			ypos += self.getFieldHeight( curr_field );
		raise ReferenceError( "Field not found!" );
	
	def draw( self ):
		curr_y = 3;
		
		for field in self.fields:
			value = unicode( getattr( self.mm, field.name ) );
			
			self.win.addstr( curr_y, 1, field.verbose_name.encode(locale.getpreferredencoding()) );
			
			height = self.getFieldHeight( field );
			winsize = self.win.getmaxyx();
			
			editwin = self.win.subwin( height, winsize[1]-31, self.pos[1] + curr_y, self.pos[0] + 30 );
			editwin.keypad(1);
			editwin.addstr( value.encode(locale.getpreferredencoding()) );
			editbox = Textbox( editwin );
			
			self.editors[field.name] = ( editwin, editbox );
			
			curr_y += height;
	
	def enter( self ):
		self.selIdx = 0;
		self.selMax = len( self.fields ) - 1;
		
		while( True ):
			# Highlight selected field label
			field = self.fields[self.selIdx];
			
			self.win.addstr(
				self.getFieldYPos(field), 1,
				field.verbose_name.encode(locale.getpreferredencoding()),
				curses.A_STANDOUT
				);
			self.win.refresh();
			
			key = self.win.getch();
			
			if key == curses.KEY_UP and self.selIdx > 0:
				self.selIdx -= 1;
			
			elif key == curses.KEY_DOWN and self.selIdx < self.selMax:
				self.selIdx += 1;
			
			elif key in ( ord('q'), ord('Q') ):
				return;
			
			elif key in ( ord('s'), ord('S') ):
				try:
					self.mm.save();
				except Exception, instance:
					msg = unicode( instance );
				else:
					msg = "Your settings have been saved.";
				self.win.addstr( 1, 5, msg.encode(locale.getpreferredencoding()) );
			
			elif key in ( curses.KEY_RIGHT, curses.KEY_ENTER, ord('\n') ):
				valid = False;
				while not valid:
					self.editors[field.name][1].edit();
					try:
						setattr( self.mm, field.name,
							field.to_python( self.editors[field.name][1].gather().strip() )
							);
					except ValidationError, instance:
						msg = unicode( instance );
						self.win.addstr( 1, 5, msg.encode(locale.getpreferredencoding()), curses.A_STANDOUT );
						self.win.refresh();
					else:
						valid = True;
						self.win.move( 1, 5 );
						self.win.clrtoeol();
				
				self.editors[field.name][0].refresh();
			
			self.win.addstr(
				self.getFieldYPos(field), 1,
				field.verbose_name.encode(locale.getpreferredencoding())
				);


class WndUsers( BaseWindow ):
	tabName = 'Registered users';
	
	def draw( self ):
		curr_y = 3;
		
		for acc in self.mm.mumbleuser_set.all():
			self.win.addstr( curr_y, 1, acc.name.encode(locale.getpreferredencoding()) );
			curr_y += 1;
	


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
	
	myname = "Mumble Commander";
	
	while( True ):
		selectedObj = mumbles[selectedIdx];
		
		maxyx = stdscr.getmaxyx();
		stdscr.addstr( 0, maxyx[1] / 2 - len(myname)/2, myname, curses.A_UNDERLINE );
		
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
			stdscr.addstr( 0, maxyx[1] / 2 - len(myname)/2, myname, curses.A_UNDERLINE );
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













