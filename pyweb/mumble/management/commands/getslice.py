# -*- coding: utf-8 -*-

"""
 *  Copyright © 2009-2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

import re

from os 	import listdir
from os.path	import join

from urllib	import urlopen

from django.core.management.base	import BaseCommand
from django.conf			import settings


HEAD_SLICE_URL = 'http://mumble.git.sourceforge.net/git/gitweb.cgi?p=mumble/mumble;a=blob_plain;f=src/murmur/Murmur.ice;hb=HEAD'


class Command( BaseCommand ):
	def handle(self, **options):
		nameregex = re.compile( "Murmur_(\d)-(\d)-(\d).ice" )
		basepath  = join( settings.MUMBLE_DJANGO_ROOT, 'pyweb', 'mumble' )
		version   = [0, 0, 0]
		
		for filename in listdir( basepath ):
			match = nameregex.match( filename )
			if match:
				for idx in range(3):
					namedigit = int( match.group(idx + 1) )
					if version[idx] < namedigit:
						version = [
							int( match.group(1) ),
							int( match.group(2) ),
							int( match.group(3) ),
							]
						break
		
		version[2] += 1
		
		userversion = raw_input( "Enter current HEAD version [%d.%d.%d]: " % tuple(version) )
		if userversion:
			version = [ int(digit) for digit in userversion.split('.') ]
		
		slicefile = join( settings.MUMBLE_DJANGO_ROOT, 'pyweb', 'mumble', 'Murmur_%d-%d-%d.ice' % tuple(version) )
		
		gitfile = urlopen( HEAD_SLICE_URL ).fp.read();
		
		slicefd = open( slicefile, 'wb' );
		slicefd.write( gitfile );
		slicefd.close();



