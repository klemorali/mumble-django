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

from django import template

register = template.Library();

### FILTER: mrange -- used to render the ||| lines in the channel tree

def mrange( value ):
	"If value > 1, returns range( value - 1 ), else returns an empty list."
	val = int( value );
	if( val > 1 ):
		return range( val - 1 );
	return list();

register.filter( 'mrange', mrange );

### FILTER: trunc -- converts "a very very extaordinary long text" to "a very very extra..."
def trunc( string, maxlen = 50 ):
	if len(string) < maxlen:
		return string;
	return string[:(maxlen - 3)] + "...";

register.filter( 'trunc', trunc );
