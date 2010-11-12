﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Run the embedded Django server and point the web browser to it. """

import webbrowser, sys, os
from django.core.servers.basehttp import run, AdminMediaHandler, WSGIServerException
from django.core.handlers.wsgi import WSGIHandler
from os.path import join, dirname, abspath, exists

MUMBLE_DJANGO_ROOT = None

# Path auto-detection
if not MUMBLE_DJANGO_ROOT or not exists( MUMBLE_DJANGO_ROOT ):
    MUMBLE_DJANGO_ROOT = dirname(abspath(__file__))

# environment variables
sys.path.append( MUMBLE_DJANGO_ROOT )
sys.path.append( join( MUMBLE_DJANGO_ROOT, 'pyweb' ) )

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PORT = 8000

    try:
        HANDLER = AdminMediaHandler(WSGIHandler(), '')

        webbrowser.open('http://localhost:%s' % PORT)
        run('0.0.0.0', PORT, HANDLER)

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