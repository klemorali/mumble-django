#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 *  Copyright © 2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *  Copyright © 2010, Harry "nodefab" Gabriel <rootdesign@gmail.com>
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

import webbrowser, sys, os
from django.core.servers.basehttp import run, AdminMediaHandler, WSGIServerException
from django.core.handlers.wsgi import WSGIHandler
from os.path import join, dirname, abspath, exists
from optparse import OptionParser

MUMBLE_DJANGO_ROOT = None

# Path auto-detection
if not MUMBLE_DJANGO_ROOT or not exists( MUMBLE_DJANGO_ROOT ):
    MUMBLE_DJANGO_ROOT = dirname(abspath(__file__))

# environment variables
sys.path.append( MUMBLE_DJANGO_ROOT )
sys.path.append( join( MUMBLE_DJANGO_ROOT, 'pyweb' ) )

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    
    # parse argv to options
    OPARSER = OptionParser()
    OPARSER.add_option("-i", "--ip", dest="addr", default="127.0.0.1")
    OPARSER.add_option("-p", "--port", dest="port", type="int", default="8080")
    (OPTIONS, ARGS) = OPARSER.parse_args()

    try:
        HANDLER = AdminMediaHandler(WSGIHandler(), '')

        webbrowser.open('http://%s:%s' % (OPTIONS.addr, OPTIONS.port))
        run(OPTIONS.addr, OPTIONS.port, HANDLER)

    except WSGIServerException, e:
        # Use helpful error messages instead of ugly tracebacks.
        ERRORS = {
            13: "You don't have permission to access that port.",
            98: "That port is already in use.",
            99: "That IP address can't be assigned-to.",
        }
        try:
            ERROR_TEXT = ERRORS[e.args[0].args[0]]
        except (AttributeError, KeyError):
            ERROR_TEXT = str(e)
        sys.stderr.write("Error: %s \n" % ERROR_TEXT)