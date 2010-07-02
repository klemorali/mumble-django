# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 200, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

import simplejson
import inspect
import functools
import traceback
from sys import stderr

from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.defaults import patterns
from django.core.urlresolvers  import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt


def getname( cls_or_name ):
    if type(cls_or_name) not in ( str, unicode ):
        return cls_or_name.__name__
    return cls_or_name

class Provider( object ):
    """ Provider for Ext.Direct. This class handles building API information and
        routing requests to the appropriate functions, and serializing their
        response and exceptions - if any.

        Instantiation:
        >>> EXT_JS_PROVIDER = Provider( [name="Ext.app.REMOTING_API", autoadd=True] )

        If autoadd is True, the api.js will include a line like such:
            Ext.Direct.addProvider( Ext.app.REMOTING_API );

        After instantiating the Provider, register functions to it like so:

        >>> @EXT_JS_PROVIDER.register_method("myclass")
            def myview( request, possibly, some, other, arguments ):
               " does something with all those args and returns something "
               return 13.37

        Note that those views **MUST NOT** return an HttpResponse but simply
        the plain result, as the Provider will build a response from whatever
        your view returns!

        To be able to access the Provider, include its URLs in an arbitrary
        URL pattern, like so:

        >>> from views import EXT_JS_PROVIDER # import our provider instance
        >>> urlpatterns = patterns(
                # other patterns go here
                ( r'api/', include(EXT_DIRECT_PROVIDER.urls) ),
            )

        This way, the Provider will define the URLs "api/api.js" and "api/router".

        If you then access the "api/api.js" URL, you will get a response such as:
            Ext.app.REMOTING_API = { # Ext.app.REMOTING_API is from Provider.name
                "url": "/mumble/api/router",
                "type": "remoting",
                "actions": {"myclass": [{"name": "myview", "len": 4}]}
                }

        You can then use this code in ExtJS to define the Provider there.
    """

    def __init__( self, name="Ext.app.REMOTING_API", autoadd=True ):
        self.name     = name
        self.autoadd  = autoadd
        self.classes  = {}

    def register_method( self, cls_or_name ):
        """ Return a function that takes a method as an argument and adds that to cls_or_name. """
        clsname = getname(cls_or_name)
        if clsname not in self.classes:
            self.classes[clsname] = {}
        return functools.partial( self._register_method, cls_or_name )

    def _register_method( self, cls_or_name, method ):
        """ Actually registers the given function as a method of cls_or_name. """
        self.classes[ getname(cls_or_name) ][ method.__name__ ] = method
        method.EXT_argnames = inspect.getargspec( method ).args[1:]
        method.EXT_len      = len( method.EXT_argnames )
        return method

    @csrf_exempt
    def get_api( self, request ):
        """ Introspect the methods and get a JSON description of this API. """
        actdict = {}
        for clsname in self.classes:
            actdict[clsname] = []
            for methodname in self.classes[clsname]:
                actdict[clsname].append( {
                    "name": methodname,
                    "len":  self.classes[clsname][methodname].EXT_len
                    } )

        lines = ["%s = %s;" % ( self.name, simplejson.dumps({
            "url":     reverse( self.request ),
            "type":    "remoting",
            "actions": actdict
            }))]

        if self.autoadd:
            lines.append( "Ext.Direct.addProvider( %s );" % self.name )

        return HttpResponse( "\n".join( lines ), mimetype="text/javascript" )

    @csrf_exempt
    def request( self, request ):
        """ Implements the Router part of the Ext.Direct specification.

            It handles decoding requests, calling the appropriate function (if
            found) and encoding the response / exceptions.
        """
        try:
            rawjson = [{
                'action':  request.POST['extAction'],
                'method':  request.POST['extMethod'],
                'data':    request.POST['extData'],
                'type':    request.POST['extType'],
                'tid':     request.POST['extTID'],
            }]
        except (MultiValueDictKeyError, KeyError):
            rawjson  = simplejson.loads( request.raw_post_data )
            if not isinstance( rawjson, list ):
                rawjson = [rawjson]

        responses = []

        for reqinfo in rawjson:
            cls, methname, data, rtype, tid = (reqinfo['action'],
                reqinfo['method'],
                reqinfo['data'],
                reqinfo['type'],
                reqinfo['tid'])

            if cls not in self.classes:
                responses.append({
                    'type':    'exception',
                    'message': 'no such action',
                    'where':   cls,
                    "tid":     tid,
                    })
                continue

            if methname not in self.classes[cls]:
                responses.append({
                    'type':    'exception',
                    'message': 'no such method',
                    'where':   methname,
                    "tid":     tid,
                    })
                continue

            func = self.classes[cls][methname]

            if func.EXT_len and len(data) == 1 and type(data[0]) == dict:
                # data[0] seems to contain a dict with params. check if it does, and if so, unpack
                args = []
                for argname in func.EXT_argnames:
                    if argname in data[0]:
                        args.append( data[0][argname] )
                    else:
                        args = None
                        break
                if args:
                    data = args

            try:
                if data:
                    result = func( request, *data )
                else:
                    result = func( request )

            except Exception, err:
                errinfo = {
                    'type': 'exception',
                    "tid":  tid,
                    }
                if settings.DEBUG:
                    traceback.print_exc( file=stderr )
                    errinfo['message'] = unicode(err)
                    errinfo['where']   = traceback.format_exc()
                else:
                    errinfo['message'] = 'Sorry, an error occurred.'
                    errinfo['where']   = ''
                responses.append(errinfo)

            else:
                responses.append({
                    "type":   rtype,
                    "tid":    tid,
                    "action": cls,
                    "method": methname,
                    "result": result
                    })

        if len(responses) == 1:
            return HttpResponse( simplejson.dumps( responses[0] ), mimetype="text/javascript" )
        else:
            return HttpResponse( simplejson.dumps( responses ),    mimetype="text/javascript" )

    @property
    def urls(self):
        """ Return the URL patterns. """
        return patterns('',
            (r'api.js$',  self.get_api ),
            (r'router/?', self.request ),
            )

