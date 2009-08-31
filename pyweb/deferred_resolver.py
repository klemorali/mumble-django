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

class ViewResolver( object ):
	def __init__( self, string, *args, **kwargs ):
		self._string = string;
		self._args   = args;
		self._kwargs = kwargs;
	
	def __str__( self ):
		from django.core.urlresolvers import reverse
		return reverse( self._string, *self._args, **self._kwargs );
	
	def __add__( self, other ):
		return str( self ) + other;
