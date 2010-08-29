# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *
 *  djExtDirect is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

import simplejson
import httplib
from threading import Lock
from urlparse import urljoin, urlparse

def lexjs(javascript):
    """ Parse the given javascript and return a dict of variables defined in there. """
    ST_NAME, ST_ASSIGN = range(2)
    state = ST_NAME
    foundvars = {}
    buf = ""
    name = ""

    for char in javascript:
        if state == ST_NAME:
            if   char == ' ':
                continue
            elif char == '=':
                state = ST_ASSIGN
                name = buf
                buf = ""
            elif char == ';':
                state = ST_NAME
                buf = ""
            else:
                buf += char

        elif state == ST_ASSIGN:
            if   char == ';':
                state = ST_NAME
                foundvars[name] = simplejson.loads(buf)
                name = ""
                buf  = ""
            else:
                buf += char

    return foundvars

class RequestError(Exception):
    """ Raised if the request returned a status code other than 200. """
    pass

class ReturnedError(Exception):
    """ Raised if the "type" field in the response is "exception". """
    pass

class Client(object):
    """ Ext.Direct client side implementation.

        This class handles parsing an API specification, building proxy objects from it,
        and making calls to the router specified in the API.

        Instantiation:

        >>> cli = Client( "http://localhost:8000/mumble/api/api.js", "Ext.app.REMOTING_API" )

        The apiname parameter defaults to ``Ext.app.REMOTING_API`` and is used to select
        the proper API variable from the API source.

        The client will then create proxy objects for each action defined in the URL,
        which are accessible as properties of the Client instance. Suppose your API defines
        the ``Accounts`` and ``Mumble`` actions, then the client will provide those as such:

        >>> cli.Accounts
        <client.AccountsPrx object at 0x93d9e2c>
        >>> cli.Mumble
        <client.MumblePrx object at 0x93d9a2c>

        These objects provide native Python methods for each method defined in the actions:

        >>> cli.Accounts.login
        <bound method AccountsPrx.login of <client.AccountsPrx object at 0x93d9e2c>>

        So, in order to make a call over Ext.Direct, you would simply call the proxy method:

        >>> cli.Accounts.login( "svedrin", "passwort" )
        {'success': True}
    """

    def __init__( self, apiurl, apiname="Ext.app.REMOTING_API", cookie=None ):
        self.apiurl  = apiurl
        self.apiname = apiname
        self.cookie  = cookie

        purl = urlparse( self.apiurl )
        conn = httplib.HTTPConnection( purl.netloc )
        conn.putrequest( "GET", purl.path )
        conn.endheaders()
        resp = conn.getresponse()
        conn.close()
        foundvars = lexjs( resp.read() )

        self.api = foundvars[apiname]
        self.routerurl = urljoin( self.apiurl, self.api["url"] )

        self._tid = 1
        self._tidlock = Lock()

        for action in self.api['actions']:
            setattr( self, action, self.get_object(action) )

    @property
    def tid( self ):
        """ Thread-safely get a new TID. """
        self._tidlock.acquire()
        self._tid += 1
        newtid = self._tid
        self._tidlock.release()
        return newtid

    def call( self, action, method, *args ):
        """ Make a call to Ext.Direct. """
        reqtid = self.tid
        data=simplejson.dumps({
            'tid':    reqtid,
            'action': action,
            'method': method,
            'data':   args,
            'type':   'rpc'
            })

        purl = urlparse( self.routerurl )
        conn = httplib.HTTPConnection( purl.netloc )
        conn.putrequest( "POST", purl.path )
        conn.putheader( "Content-Type", "application/json" )
        conn.putheader( "Content-Length", len(data) )
        if self.cookie:
            conn.putheader( "Cookie", self.cookie )
        conn.endheaders()
        conn.send( data )
        resp = conn.getresponse()
        conn.close()

        if resp.status != 200:
            raise RequestError( resp.status, resp.reason )

        respdata = simplejson.loads( resp.read() )
        if respdata['type'] == 'exception':
            raise ReturnedError( respdata['message'], respdata['where'] )
        if respdata['tid'] != reqtid:
            raise RequestError( 'TID mismatch' )

        cookie = resp.getheader( "set-cookie" )
        if cookie:
            self.cookie = cookie.split(';')[0]

        return respdata['result']

    def get_object( self, action ):
        """ Return a proxy object that has methods defined in the API. """

        def makemethod( methspec ):
            def func( self, *args ):
                if len(args) != methspec['len']:
                    raise TypeError( '%s() takes exactly %d arguments (%d given)' % (
                        methspec['name'], methspec['len'], len(args)
                        ) )
                return self._cli.call( action, methspec['name'], *args )

            func.__name__ = methspec['name']
            return func

        def init( self, cli ):
            self._cli = cli

        attrs = {
                '__init__': init
            }

        for methspec in self.api['actions'][action]:
            attrs[methspec['name']] = makemethod( methspec )

        return type( action+"Prx", (object,), attrs )( self )
