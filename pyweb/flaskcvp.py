#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

import getpass
from optparse import OptionParser

from flask import Flask, jsonify

from mumble.mctl import MumbleCtlBase

DEFAULT_CONNSTRING = 'Meta:tcp -h 127.0.0.1 -p 6502'
DEFAULT_SLICEFILE  = '/usr/share/slice/Murmur.ice'
DEFAULT_ICESECRET  = None

if __name__ == '__main__':
    parser = OptionParser("""Usage: %prog [options]

This is a minimalistic implementation of a Channel Viewer Protocol provider
using the Flask Python framework and Mumble-Django's MCTL connection library.
""")

    parser.add_option( "-c", "--connstring",
        help="connection string to use. Default is '%s'." % DEFAULT_CONNSTRING,
        default=None
        )

    parser.add_option( "-i", "--icesecret",
        help="Ice secret to use in the connection. Also see --asksecret.",
        default=DEFAULT_ICESECRET
        )

    parser.add_option( "-a", "--asksecret",
        help="Ask for the Ice secret on the shell instead of taking it from the command line.",
        action="store_true", default=False
        )

    parser.add_option( "-s", "--slice",
        help="path to the slice file. Default is '%s'." % DEFAULT_SLICEFILE,
        default=None
        )

    parser.add_option( "-d", "--debug", 
        help="Enable error debugging",
        default=False, action="store_true" )

    parser.add_option( "-H", "--host",
        help="The IP to bind to. Default is '127.0.0.1'.",
        default="127.0.0.1"
        )

    parser.add_option( "-p", "--port", type="int",
        help="The port number to bind to. Default is 5000.",
        default=5000
        )

    options, progargs = parser.parse_args()

    if options.connstring is None:
        options.connstring = DEFAULT_CONNSTRING

    if options.slice is None:
        options.slice = DEFAULT_SLICEFILE

    if options.asksecret:
        options.icesecret = getpass.getpass( "Ice secret: " )

else:
    class options:
        connstring = DEFAULT_CONNSTRING
        slice      = DEFAULT_SLICEFILE
        icesecret  = DEFAULT_ICESECRET

ctl = MumbleCtlBase.newInstance( options.connstring, options.slice, options.icesecret )


app = Flask(__name__)

def getUser(user):
    fields = ["channel", "deaf", "mute", "name", "selfDeaf", "selfMute",
        "session", "suppress", "userid", "idlesecs", "recording", "comment",
        "prioritySpeaker"]
    return dict(zip(fields, [getattr(user, field) for field in fields]))

def getChannel(channel):
    fields = ["id", "name", "parent", "links", "description", "temporary", "position"]
    data = dict(zip(fields, [getattr(channel.c, field) for field in fields]))
    data['channels'] = [ getChannel(subchan) for subchan in channel.children ]
    data['users']    = [ getUser(user) for user in channel.users ]
    return data

@app.route('/<int:srv_id>')
def getTree(srv_id):
    name = ctl.getConf(srv_id, "registername")
    tree = ctl.getTree(srv_id)

    serv = {
        'id':   srv_id,
        'name': name,
        'root': getChannel(tree)
        }

    return jsonify(serv)

@app.route('/')
def getServers():
    return jsonify(servers=ctl.getBootedServers())

if __name__ == '__main__':
    app.run(host=options.host, port=options.port, debug=options.debug)
