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
import inspect
import functools
import traceback
from sys import stderr

from django      import forms
from django.http import HttpResponse, Http404
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers  import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe

__author__ = "Michael Ziegler"
__copyright__ = "Copyright (C) 2010, Michael Ziegler"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "diese-addy@funzt-halt.net"
__status__ = "Development"


def getname( cls_or_name ):
    if type(cls_or_name) not in ( str, unicode ):
        return cls_or_name.__name__
    return cls_or_name


# Template used for the auto-generated form classes
EXT_CLASS_TEMPLATE = """
Ext.namespace('Ext.ux');

Ext.ux.%(clsname)s = function( config ){
    Ext.apply( this, config );

    var defaultconf = %(defaultconf)s;

    Ext.applyIf( this, defaultconf );
    this.initialConfig = defaultconf;

    Ext.ux.%(clsname)s.superclass.constructor.call( this );

    this.form.api = %(apiconf)s;
    this.form.paramsAsHash = true;

    if( typeof config.pk != "undefined" ){
        this.load();
    }
}

Ext.extend( Ext.ux.%(clsname)s, Ext.form.FormPanel, {
    load: function(){
        this.getForm().load({ params: Ext.applyIf( {pk: this.pk}, this.baseParams ) });
    },
    submit: function(){
        this.getForm().submit({
            params: Ext.applyIf( {pk: this.pk}, this.baseParams ),
            failure: function( form, action ){
                if( action.failureType == Ext.form.Action.SERVER_INVALID &&
                    typeof action.result.errors[''] != 'undefined' ){
                    Ext.Msg.alert( "Error", action.result.errors[''] );
                }
            }
        });
    },
} );

Ext.reg( '%(clslowername)s', Ext.ux.%(clsname)s );
"""
# About the this.form.* lines, see
# http://www.sencha.com/forum/showthread.php?96001-solved-Ext.Direct-load-data-in-extended-Form-fails-%28scope-issue%29

class Provider( object ):
    """ Provider for Ext.Direct. This class handles building API information and
        routing requests to the appropriate functions, and serializing their
        response and exceptions - if any.

        Instantiation:

        >>> EXT_JS_PROVIDER = Provider( [name="Ext.app.REMOTING_API", autoadd=True] )

        If autoadd is True, the api.js will include a line like such::

            Ext.Direct.addProvider( Ext.app.REMOTING_API );

        After instantiating the Provider, register functions to it like so:

        >>> @EXT_JS_PROVIDER.register_method("myclass")
        ... def myview( request, possibly, some, other, arguments ):
        ...    " does something with all those args and returns something "
        ...    return 13.37

        Note that those views **MUST NOT** return an HttpResponse but simply
        the plain result, as the Provider will build a response from whatever
        your view returns!

        To be able to access the Provider, include its URLs in an arbitrary
        URL pattern, like so:

        >>> from views import EXT_JS_PROVIDER # import our provider instance
        >>> urlpatterns = patterns(
        ...     # other patterns go here
        ...     ( r'api/', include(EXT_DIRECT_PROVIDER.urls) ),
        ... )

        This way, the Provider will define the URLs "api/api.js" and "api/router".

        If you then access the "api/api.js" URL, you will get a response such as::

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
        self.forms    = {}

    def register_method( self, cls_or_name, flags={} ):
        """ Return a function that takes a method as an argument and adds that
            to cls_or_name.

            The flags parameter is for additional information, e.g. formHandler=True.

            Note: This decorator does not replace the method by a new function,
            it returns the original function as-is.
        """
        return functools.partial( self._register_method, cls_or_name, flags=flags )

    def _register_method( self, cls_or_name, method, flags={} ):
        """ Actually registers the given function as a method of cls_or_name. """
        clsname = getname(cls_or_name)
        if clsname not in self.classes:
            self.classes[clsname] = {}
        self.classes[ clsname ][ method.__name__ ] = method
        method.EXT_argnames = inspect.getargspec( method ).args[1:]
        method.EXT_len      = len( method.EXT_argnames )
        method.EXT_flags    = flags
        return method

    def register_form( self, formclass ):
        """ Register a Django Form class.

            After registration, you will be able to retrieve an ExtJS form class
            definition for this form under the URL "<formname>.js". Include this
            script via a <script> tag just like the "api.js" for Ext.Direct.

            The form class will then be created as Ext.ux.<FormName> and will
            have a registered xtype of "formname".

            When registering a form, the Provider will automatically generate and
            export objects and methods for data transfer, so the form will be
            ready to use.

            To ensure that validation error messages are displayed properly, be
            sure to call Ext.QuickTips.init() somewhere in your code.

            In order to do extra validation, the Provider checks if your form class
            has a method called EXT_validate, and if so, calls that method with the
            request as parameter before calling is_valid() or save(). If EXT_validate
            returns False, the form will not be saved and an error will be returned
            instead. EXT_validate should update form.errors before returning False.
        """
        if not issubclass( formclass, forms.ModelForm ):
            raise TypeError( "Ext.Direct provider can only handle ModelForms, '%s' is something else." % formclass.__name__ )

        formname = formclass.__name__.lower()
        self.forms[formname] = formclass

        getfunc = functools.partial( self.get_form_data, formname )
        getfunc.EXT_len = 1
        getfunc.EXT_argnames = ["pk"]
        getfunc.EXT_flags = {}

        updatefunc = functools.partial( self.update_form_data, formname )
        updatefunc.EXT_len = 1
        updatefunc.EXT_argnames = ["pk"]
        updatefunc.EXT_flags = { 'formHandler': True }

        self.classes["XD_%s"%formclass.__name__] = {
            "get":    getfunc,
            "update": updatefunc,
            }

        return formclass

    @csrf_exempt
    def get_api( self, request ):
        """ Introspect the methods and get a JSON description of this API. """
        actdict = {}
        for clsname in self.classes:
            actdict[clsname] = []
            for methodname in self.classes[clsname]:
                methinfo = {
                    "name": methodname,
                    "len":  self.classes[clsname][methodname].EXT_len
                    }
                methinfo.update( self.classes[clsname][methodname].EXT_flags )
                actdict[clsname].append( methinfo )

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
        # First try to use request.POST, if that doesn't work check for req.raw_post_data.
        # The other way round this might make more sense because the case that uses
        # raw_post_data is way more common, but accessing request.POST after raw_post_data
        # causes issues with Django's test client while accessing raw_post_data after
        # request.POST does not.
        try:
            jsoninfo = {
                'action':  request.POST['extAction'],
                'method':  request.POST['extMethod'],
                'type':    request.POST['extType'],
                'upload':  request.POST['extUpload'],
                'tid':     request.POST['extTID'],
            }
        except (MultiValueDictKeyError, KeyError), err:
            try:
                rawjson = simplejson.loads( request.raw_post_data )
            except simplejson.JSONDecodeError:
                return HttpResponse( simplejson.dumps({
                    'type':    'exception',
                    'message': 'malformed request',
                    'where':   unicode(err),
                    "tid":     None, # dunno
                    }), mimetype="text/javascript" )
            else:
                return self.process_normal_request( request, rawjson )
        else:
            return self.process_form_request( request, jsoninfo )

    def process_normal_request( self, request, rawjson ):
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

            if data is not None:
                datalen = len(data)
            else:
                datalen = 0

            if datalen != len(func.EXT_argnames):
                responses.append({
                    'type': 'exception',
                    'tid':  tid,
                    'message': 'invalid arguments',
                    'where': 'Expected %d, got %d' % ( len(func.EXT_argnames), len(data) )
                    })
                continue

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
                    errinfo['message'] = 'The socket packet pocket has an error to report.'
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

    def process_form_request( self, request, reqinfo ):
        """ Router for POST requests that submit form data and/or file uploads. """
        cls, methname, rtype, tid = (reqinfo['action'],
            reqinfo['method'],
            reqinfo['type'],
            reqinfo['tid'])

        if cls not in self.classes:
            response = {
                'type':    'exception',
                'message': 'no such action',
                'where':   cls,
                "tid":     tid,
                }

        elif methname not in self.classes[cls]:
            response = {
                'type':    'exception',
                'message': 'no such method',
                'where':   methname,
                "tid":     tid,
                }

        else:
            func = self.classes[cls][methname]
            try:
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
                    errinfo['message'] = 'The socket packet pocket has an error to report.'
                    errinfo['where']   = ''
                response = errinfo

            else:
                response = {
                    "type":   rtype,
                    "tid":    tid,
                    "action": cls,
                    "method": methname,
                    "result": result
                    }

        if reqinfo['upload'] == "true":
            return HttpResponse(
                "<html><body><textarea>%s</textarea></body></html>" % simplejson.dumps(response),
                mimetype="text/javascript"
                )
        else:
            return HttpResponse( simplejson.dumps( response ), mimetype="text/javascript" )

    def get_form( self, request, formname ):
        """ Convert the form given in "formname" to an ExtJS FormPanel. """

        if formname not in self.forms:
            raise Http404(formname)

        items = []
        clsname = self.forms[formname].__name__
        hasfiles = False

        for fldname in self.forms[formname].base_fields:
            field = self.forms[formname].base_fields[fldname]
            extfld = {
                "fieldLabel": field.label is not None and unicode(field.label) or fldname,
                "name":       fldname,
                "xtype":     "textfield",
                #"allowEmpty": field.required,
                }

            if hasattr( field, "choices" ) and field.choices:
                extfld.update({
                    "name":       fldname,
                    "hiddenName": fldname,
                    "xtype":      "combo",
                    "store":      field.choices,
                    "typeAhead":  True,
                    "emptyText":  'Select...',
                    "triggerAction": 'all',
                    "selectOnFocus": True,
                    })
            elif isinstance( field, forms.BooleanField ):
                extfld.update({
                    "xtype": "checkbox"
                    })
            elif isinstance( field, forms.IntegerField ):
                extfld.update({
                    "xtype": "numberfield",
                    })
            elif isinstance( field, forms.FileField ) or isinstance( field, forms.ImageField ):
                hasfiles = True
                extfld.update({
                    "xtype":     "textfield",
                    "inputType": "file"
                    })
            elif isinstance( field.widget, forms.Textarea ):
                extfld.update({
                    "xtype": "textarea",
                    })
            elif isinstance( field.widget, forms.PasswordInput ):
                extfld.update({
                    "xtype":     "textfield",
                    "inputType": "password"
                    })

            items.append( extfld )

            if field.help_text:
                items.append({
                    "xtype": "label",
                    "text":  unicode(field.help_text),
                    "cls":   "form_hint_label",
                    })

        clscode = EXT_CLASS_TEMPLATE % {
            'clsname':      clsname,
            'clslowername': formname,
            'defaultconf':  '{'
                'items:'    + simplejson.dumps(items, indent=4) + ','
                'fileUpload: ' + simplejson.dumps(hasfiles) + ','
                'defaults: { "anchor": "-20px" },'
                'paramsAsHash: true,'
                'baseParams: {},'
                'autoScroll: true,'
                """buttons: [{
                        text:    "Submit",
                        handler: this.submit,
                        scope:   this
                    }]"""
                '}',
            'apiconf': ('{'
                'load:  ' + ("XD_%s.get"    % clsname) + ","
                'submit:' + ("XD_%s.update" % clsname) + ","
                "}"),
            }

        return HttpResponse( mark_safe( clscode ), mimetype="text/javascript" )

    def get_form_data( self, formname, request, pk ):
        formcls  = self.forms[formname]
        if pk != -1:
            instance = formcls.Meta.model.objects.get( pk=pk )
        else:
            instance = None
        forminst = formcls( instance=instance )

        if hasattr( forminst, "EXT_authorize" ) and \
           forminst.EXT_authorize( request, "get" ) is False:
            return { 'success': False, 'errors': {'': 'access denied'} }

        data = {}
        for fld in forminst.fields:
            data[fld] = getattr( instance, fld )
        return { 'data': data, 'success': True }

    def update_form_data( self, formname, request ):
        pk = int(request.POST['pk'])
        formcls  = self.forms[formname]
        if pk != -1:
            instance = formcls.Meta.model.objects.get( pk=pk )
        else:
            instance = None
        if request.POST['extUpload'] == "true":
            forminst = formcls( request.POST, request.FILES, instance=instance )
        else:
            forminst = formcls( request.POST, instance=instance )

        if hasattr( forminst, "EXT_authorize" ) and \
           forminst.EXT_authorize( request, "update" ) is False:
            return { 'success': False, 'errors': {'': 'access denied'} }

        # save if either no usable validation method available or validation passes; and form.is_valid
        if ( hasattr( forminst, "EXT_validate" ) and callable( forminst.EXT_validate )
             and not forminst.EXT_validate( request ) ):
            return { 'success': False, 'errors': {'': 'pre-validation failed'} }

        if forminst.is_valid():
            forminst.save()
            return { 'success': True }
        else:
            errdict = {}
            for errfld in forminst.errors:
                errdict[errfld] = "\n".join( forminst.errors[errfld] )
            return { 'success': False, 'errors': errdict }

    @property
    def urls(self):
        """ Return the URL patterns. """
        pat =  patterns('',
            (r'api.js$',  self.get_api ),
            (r'router/?', self.request ),
            )
        if self.forms:
            pat.append( url( r'(?P<formname>\w+).js$', self.get_form ) )
        return pat
