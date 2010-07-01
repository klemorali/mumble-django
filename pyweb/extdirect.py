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

import simplejson
import inspect
import functools

from django.http import HttpResponse

def getname( cls_or_name ):
    if type(cls_or_name) not in ( str, unicode ):
        return cls_or_name.__name__
    return cls_or_name

class Provider( object ):
    def __init__( self, base_url ):
        self.base_url = base_url
        self.classes = {}
    
    def register_instance( self, cls_or_name, instance ):
        name = getname(cls_or_name)
        if name not in self.classes:
            raise KeyError(name)
        self.classes[ name ][0] = instance
        return instance
    
    def register_method( self, cls_or_name ):
        """ Return a function that takes a method as an argument and adds that to cls_or_name. """
        print "REGMETHOD", cls_or_name
        clsname = getname(cls_or_name)
        if clsname not in self.classes:
            self.classes[clsname] = ( None, {} )
        return functools.partial( self._register_method, cls_or_name )
    
    def _register_method( self, cls_or_name, method ):
        print "REGREALMETHOD", cls_or_name, method
        self.classes[ getname(cls_or_name) ][1][ method.__name__ ] = method
        return method
    
    def get_api( self, name="Ext.app.REMOTING_API" ):
        """ Introspect the methods and get a JSON description of this API. """
        actdict = {}
        for clsname in self.classes:
            actdict[clsname] = []
            for methodname in self.classes[clsname][1]:
                actdict[clsname].append( {
                    "name": methodname,
                    "len":  len( inspect.getargspec( self.classes[clsname][1][methodname] ).args )
                    } )
        
        return "%s = %s" % ( name, simplejson.dumps({
            "url":     ("%s/router" % self.base_url),
            "type":    "remoting",
            "actions": actdict
            }))
    
    def request( self, request ):
        cls      = request.POST['extAction']
        methname = request.POST['extMethod']
        data     = request.POST['extData']
        rtype    = request.POST['extType']
        tid      = request.POST['extTID']
        
        if cls not in self.classes:
            raise KeyError(cls)
        if methname not in self.classes[cls][1]:
            raise KeyError(methname)
        
        result = self.classes[cls][1][methname]( *data, request=request )
        
        return HttpResponse( simplejson.dumps({
            "type":   rtype,
            "tid":    tid,
            "action": cls,
            "method": methname,
            "result": result
            }))

