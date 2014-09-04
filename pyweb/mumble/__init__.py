# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;
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

version = { 'major': 2, 'minor': 12, 'beta': None }

if version['beta']:
    version_str = "v%(major)d.%(minor)dbeta%(beta)d" % version
else:
    version_str = "v%(major)d.%(minor)d" % version

def getVersions():
    """ Generator that yields all available upstream versions. """
    url = 'http://bitbucket.org/Svedrin/mumble-django/raw/tip/.hgtags'
    from urllib2 import urlopen
    webtags = urlopen(url)
    try:
        while True:
            line = webtags.readline().strip()
            if not line:
                raise StopIteration
            _, version = line.split(' ')
            yield version
    finally:
        webtags.close()

def getLatestUpstreamVersion():
    """ Return the latest version available upstream. """
    return max(getVersions())

def isUptodate():
    """ Check if this version of Mumble-Django is the latest available. """
    return version_str >= getLatestUpstreamVersion()
