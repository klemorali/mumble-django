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

try:
    import simplejson
except ImportError:
    import json as simplejson

import functools

from django      import forms
from django.http import HttpResponse, Http404
from django.conf.urls.defaults import url
from django.utils.safestring import mark_safe

from provider import Provider

# Template used for the auto-generated form classes
EXT_CLASS_TEMPLATE = """
Ext.namespace('Ext.ux');

Ext.ux.%(clsname)s = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        defaults: { "anchor": "-20px" },
        paramsAsHash: true,
        baseParams: {},
        autoScroll: true,
        submitButtonText: "Submit"
        } );
    Ext.applyIf( this, {
        buttons: [{
                text:    this.submitButtonText,
                handler: this.submit,
                id:      '%(clsname)s_submit',
                scope:   this
            }]
        });

    var defaultconf = %(defaultconf)s;

    Ext.applyIf( this, defaultconf );
    this.initialConfig = defaultconf;

    this.api = %(apiconf)s;

    Ext.ux.%(clsname)s.superclass.constructor.call( this );

    this.form.api = this.api;
    this.form.paramsAsHash = true;

    if( typeof config.pk != "undefined" ){
        this.load();
    }

    this.form.addEvents({
        'submitSuccess': true,
        'submitFailure': true
    });

    if( typeof config.listeners != "undefined" ){
        if( typeof config.listeners.submitSuccess != "undefined" )
            this.form.on("submitSuccess", config.listeners.submitSuccess);
        if( typeof config.listeners.submitFailure != "undefined" )
            this.form.on("submitFailure", config.listeners.submitFailure);
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
                    typeof action.result.errors['__all__'] != 'undefined' ){
                    Ext.Msg.alert( "Error", action.result.errors['__all__'] );
                }
                form.fireEvent("submitFailure", form, action);
            },
            success: function( form, action ){
                form.fireEvent("submitSuccess", form, action);
            }
        });
    },
} );

Ext.reg( '%(clslowername)s', Ext.ux.%(clsname)s );
"""
# About the this.form.* lines, see
# http://www.sencha.com/forum/showthread.php?96001-solved-Ext.Direct-load-data-in-extended-Form-fails-%28scope-issue%29

EXT_DYNAMICCHOICES_COMBO = """
Ext.namespace('Ext.ux');

Ext.ux.ChoicesCombo = function( config ){
    Ext.apply( this, config );

    Ext.applyIf( this, {
        displayField:   this.name,
        valueField:     this.name,
        hiddenName:     this.name,
        autoSelect:     false,
        typeAhead:      true,
        emptyText:      'Select...',
        triggerAction:  'all',
        selectOnFocus:  true,
        });

    this.triggerAction = 'all';
    this.store = new Ext.data.DirectStore({
        baseParams: {'pk': this.ownerCt.pk, 'field': this.name},
        directFn: this.ownerCt.api.choices,
        paramOrder: ['pk', 'field'],
        reader: new Ext.data.JsonReader({
            successProperty: 'success',
            idProperty: this.valueField,
            root: 'data',
            fields: [this.valueField, this.displayField]
        }),
        autoLoad: true
        });

    Ext.ux.ChoicesCombo.superclass.constructor.call( this );
    };

Ext.extend( Ext.ux.ChoicesCombo, Ext.form.ComboBox, {

    });

Ext.reg( 'choicescombo', Ext.ux.ChoicesCombo );
"""


class FormProvider(Provider):
    """ This class extends the provider class to handle Django forms.

        To export a form, register it using the ``register_form`` decorator.

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

    def __init__( self, name="Ext.app.REMOTING_API", autoadd=True ):
        Provider.__init__( self, name="Ext.app.REMOTING_API", autoadd=True )
        self.forms    = {}

    def get_choices_combo_src( self, request ):
        return HttpResponse( EXT_DYNAMICCHOICES_COMBO, mimetype="text/javascript" )

    def register_form( self, formclass ):
        """ Register a Django Form class. """
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

        choicesfunc = functools.partial( self.get_field_choices, formname )
        choicesfunc.EXT_len = 2
        choicesfunc.EXT_argnames = ["pk", "field"]
        choicesfunc.EXT_flags = {}

        self.classes["XD_%s" % formclass.__name__] = {
            "get":     getfunc,
            "update":  updatefunc,
            "choices": choicesfunc,
            }

        return formclass

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

            if hasattr( field, "choices" ):
                if field.choices:
                    # Static choices dict
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
                else:
                    # choices set but empty - load them dynamically when pk is known
                    extfld.update({
                        "name":       fldname,
                        "xtype":      "choicescombo",
                        "displayField": "v",
                        "valueField":   "k",
                        })
                    pass
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
                    "grow":  True
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
                '}',
            'apiconf': ('{'
                'load:  '  + ("XD_%s.get"     % clsname) + ","
                'submit:'  + ("XD_%s.update"  % clsname) + ","
                'choices:' + ("XD_%s.choices" % clsname) + ","
                "}"),
            }

        return HttpResponse( mark_safe( clscode ), mimetype="text/javascript" )

    def get_field_choices( self, formname, request, pk, field ):
        """ Create a bound instance of the form and return choices from the given field. """
        formcls  = self.forms[formname]
        if pk != -1:
            instance = formcls.Meta.model.objects.get( pk=pk )
        else:
            instance = None
        forminst = formcls( instance=instance )
        return {
            'success': True,
            'data': [ {'k': c[0], 'v': c[1]} for c in forminst.fields[field].choices ]
            }

    def get_form_data( self, formname, request, pk ):
        """ Called to get the current values when a form is to be displayed. """
        formcls  = self.forms[formname]
        if pk != -1:
            instance = formcls.Meta.model.objects.get( pk=pk )
        else:
            instance = None
        forminst = formcls( instance=instance )

        if hasattr( forminst, "EXT_authorize" ) and \
           forminst.EXT_authorize( request, "get" ) is False:
            return { 'success': False, 'errors': {'__all__': 'access denied'} }

        data = {}
        for fld in forminst.fields:
            if instance:
                data[fld] = getattr( instance, fld )
            else:
                data[fld] = forminst.base_fields[fld].initial
        return { 'data': data, 'success': True }

    def update_form_data( self, formname, request ):
        """ Called to update the underlying model when a form has been submitted. """
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
            return { 'success': False, 'errors': {'__all__': 'access denied'} }

        # save if either no usable validation method available or validation passes; and form.is_valid
        if ( hasattr( forminst, "EXT_validate" ) and callable( forminst.EXT_validate )
             and not forminst.EXT_validate( request ) ):
            return { 'success': False, 'errors': {'__all__': 'pre-validation failed'} }

        if forminst.is_valid():
            forminst.save()
            return { 'success': True }
        else:
            errdict = {}
            for errfld in forminst.errors:
                errdict[errfld] = "\n".join( forminst.errors[errfld] )
            return { 'success': False, 'errors': errdict }

    def get_urls(self):
        """ Return the URL patterns. """
        pat = Provider.get_urls(self)
        if self.forms:
            pat.append( url( r'choicescombo.js$',      self.get_choices_combo_src ) )
            pat.append( url( r'(?P<formname>\w+).js$', self.get_form ) )
        return pat

    urls = property(get_urls)
