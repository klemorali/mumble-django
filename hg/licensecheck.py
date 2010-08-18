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

from mercurial import hg

types_to_check = [ ".py" ];

def checkfile( filename ):
	if os.path.splitext( filename )[1] not in types_to_check:
		return True;
	try:
		fileproc = os.popen( 'licensecheck -l=100 %s' % filename );
		result = fileproc.read().strip();
		print( "Licensecheck: " + result );
		return not result.endswith( "*No copyright* UNKNOWN" );
	finally:
		fileproc.close();


def licensecheck( ui, repo, **kwargs ):
	modified, added, removed, deleted, unknown, ignored, clean = repo.status();
	
	# We only care about modified and added files.
	for curfile in (modified+added):
		fullpath = os.path.join( repo.root, curfile );
		
		if not checkfile( fullpath ):
			ui.warn( "License check failed for %s\n" % curfile );
			return True;
	
	return False;



