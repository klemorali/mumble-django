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

import os, stat

from mercurial import hg

type_whitelist = [
	'application/x-executable; charset=binary',
	'application/x-sharedlib; charset=binary',
	];

def check_mimetype( filename ):
	try:
		fileproc = os.popen( 'file -ib %s' % filename );
		mtype = fileproc.read().strip();
		return (mtype in type_whitelist);
	finally:
		fileproc.close();

def check_script( filename ):
	try:
		f = open( filename, "rb" );
		return f.read(3) == '#!/';
	finally:
		f.close();

def checkexec( ui, repo, **kwargs ):
	modified, added, removed, deleted, unknown, ignored, clean = repo.status();
	
	# We only care about modified and added files. Check their perms to see if +x
	for curfile in (modified+added):
		fullpath = os.path.join( repo.root, curfile );
		
		statinfo = os.stat( fullpath );
		mode = statinfo.st_mode;
		
		# If executable without being an executable or a script, warn and fail
		if ( (mode & stat.S_IXUSR) or (mode & stat.S_IXGRP) or (mode & stat.S_IXOTH) ) and \
		    not ( check_mimetype( fullpath ) or check_script( fullpath ) ):
			ui.warn( "Executable bit set on file %s but not ELF or script\n" % curfile );
			return True;
	
	return False;



