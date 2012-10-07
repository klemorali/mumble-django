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

import re

def iptostring(addr):
    """ Get the client's IPv4 or IPv6 address, in a pretty format. """
    if max( addr[:10] ) == 0 and addr[10:12] == (255, 255):
        return "%d.%d.%d.%d" % tuple( addr[12:] )
    ip6addr = [(hi << 8 | lo) for (hi, lo) in zip(addr[0::2], addr[1::2])]
    # colon-separated string:
    ipstr = ':'.join([ ("%x" % part) for part in ip6addr ])
    # 0:0:0 -> ::
    return re.sub( "((^|:)(0:){2,})", '::', ipstr, 1 )


class ObjectInfo( object ):
    """ Wraps arbitrary information to be easily accessed. """

    def __init__( self, **kwargs ):
        self.__dict__ = kwargs

    def __str__( self ):
        return unicode( self )

    def __repr__( self ):
        return unicode( self )

    def __unicode__( self ):
        return unicode( self.__dict__ )

    def __contains__( self, name ):
        return name in self.__dict__

    def __getitem__( self, name ):
        return self.__dict__[name]
