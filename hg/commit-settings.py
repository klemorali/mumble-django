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

def checksettings( ui, repo, **kwargs ):
	modified, added, removed, deleted, unknown, ignored, clean = repo.status();
	
	if "pyweb/settings.py" in modified + added + removed + deleted:
		resp = ui.promptchoice( 'You are about to commit settings.py. Do you want to continue? [y/N]',
			choices=('&yes', '&no'), default=1
			);
		return resp == 1;



