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

from mercurial import hg

def checkincoming( ui, repo, **kwargs ):
	url = ui.config( 'paths', 'default' );
	remote = hg.repository( ui, url );
	
	inc = repo.findincoming( remote );
	
	if inc:
		ui.status( 'Found %d incoming changesets.\n' % len(inc) );
		resp = ui.prompt( 'Do you want to abort the commit and pull/update first? [y/N]', choices=('&yes', '&no'), default='n' );
		return resp == 'y';
	else:
		ui.status( 'Found no incoming changesets, proceeding to commit.\n' );
		return False;



