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

import socket
import re

from django        import forms
from django.conf   import settings
from django.forms  import Form, ModelForm
from django.forms.models import ModelFormMetaclass
from django.utils.translation import ugettext_lazy as _

from mumble.models import MumbleServer, Mumble, MumbleUser

from djextdirect.formprovider import FormProvider

EXT_FORMS_PROVIDER = FormProvider(name="Ext.app.MUMBLE_FORMS_API")

class PropertyModelFormMeta( ModelFormMetaclass ):
    """ Metaclass that updates the property generated fields with the
        docstrings from their model counterparts.
    """
    def __init__( cls, name, bases, attrs ):
        ModelFormMetaclass.__init__( cls, name, bases, attrs )

        if cls._meta.model:
            model = cls._meta.model
        elif hasattr( bases[0], '_meta' ) and bases[0]._meta.model:
            # apparently, _meta has not been created yet if inherited, so use parent's (if any)
            model = bases[0]._meta.model
        else:
            model = None

        if model:
            mdlfields = model._meta.get_all_field_names()
            for fldname in cls.base_fields:
                if fldname in mdlfields:
                    continue
                prop = getattr( model, fldname )
                if prop.__doc__:
                    cls.base_fields[fldname].label = _(prop.__doc__)


class PropertyModelForm( ModelForm ):
    """ ModelForm that gets/sets fields that are not within the model's
        fields as model attributes. Necessary to get forms that manipulate
        properties.
    """

    __metaclass__ = PropertyModelFormMeta

    def __init__( self, *args, **kwargs ):
        ModelForm.__init__( self, *args, **kwargs )

        if self.instance:
            instfields = self.instance._meta.get_all_field_names()
            for fldname in self.fields:
                if fldname in instfields:
                    continue
                self.fields[fldname].initial = getattr( self.instance, fldname )

    def save( self, commit=True ):
        inst = ModelForm.save( self, commit=commit )

        if commit:
            self.save_to_model( inst )
        else:
            # Update when the model has been saved.
            from django.db.models import signals
            self._update_inst = inst
            signals.post_save.connect( self.save_listener, sender=inst.__class__ )

        return inst

    def save_listener( self, **kwargs ):
        if kwargs['instance'] is self._update_inst:
            self.save_to_model( self._update_inst )

    def save_to_model( self, inst ):
        instfields = inst._meta.get_all_field_names()

        for fldname in self.fields:
            if fldname not in instfields:
                setattr( inst, fldname, self.cleaned_data[fldname] )

class MumbleForm( PropertyModelForm ):
    """ The Mumble Server admin form that allows to configure settings which do
        not necessarily have to be reserved to the server hoster.

        Server hosters are expected to use the Django admin application instead,
        where everything can be configured freely.
    """

    url     = forms.CharField( required=False, help_text=_(
        "Website URL. Required for the server to be listed in the server list."))
    motd    = forms.CharField( required=False, widget=forms.Textarea )
    passwd  = forms.CharField( required=False, help_text=_(
        "Password required to join. Leave empty for public servers. Private servers cannot be listed in the server list.") )
    supw    = forms.CharField( required=False, widget=forms.PasswordInput )
    player  = forms.CharField( required=False )
    channel = forms.CharField( required=False )
    defchan = forms.TypedChoiceField( choices=(), coerce=int, required=False )
    timeout = forms.IntegerField( required=False )

    certrequired        = forms.BooleanField( required=False )
    textmessagelength   = forms.IntegerField( required=False )
    imagemessagelength  = forms.IntegerField( required=False, help_text=_(
        "In case of messages containing Base64 encoded images this overrides textmessagelength.") )
    allowhtml           = forms.BooleanField( required=False )
    rememberchannel     = forms.BooleanField( required=False, help_text=_(
        "Remember the channel users were in when they quit, and automatically move them to "
        "that channel when they join.") )
    suggestversion      = forms.CharField( required=False )
    suggestpositional   = forms.BooleanField( required=False )
    suggestpushtotalk   = forms.BooleanField( required=False )
    opusthreshold       = forms.IntegerField( required=False, initial=100, help_text=_(
        "Force Opus-Codec if this percentage of clients support it. Enter without % character.") )
    registerlocation    = forms.CharField( required=False, help_text=_(
        "Location of the server as ISO_3166-1 country code. In order for this to work, you must have "
        "a strong server certificate that carries the same country code. Alternatively, the TLD "
        "specified in the Display Address field must contain the same location code.") )
    registerpassword    = forms.CharField( required=False, help_text=_(
        "Password used for the server list registration. Required for the server to be listed in the server list. "
        "Note that you will never need to enter this password anywhere. It is solely used by Murmur to update the registration.") )
    allowping           = forms.BooleanField( required=False, initial=True, help_text=_(
        "Allow ping packets from the server (to show usercount and slots in the server browser). "
        "Required for the server to be listed in the server list.") )
    sendversion         = forms.BooleanField( required=False, initial=True, help_text=_(
        "Allow server to send system version to the client.") )


    def __init__( self, *args, **kwargs ):
        PropertyModelForm.__init__( self, *args, **kwargs )

        # Populate the `default channel' field's choices
        choices = [ ('', '----------') ]

        if self.instance and self.instance.srvid is not None:
            if self.instance.booted:
                def add_item( item, level ):
                    if item.is_server or item.is_channel:
                        choices.append( ( item.chanid, ( "-"*level + " " + item.name ) ) )

                self.instance.rootchan.visit(add_item)
            else:
                current = self.instance.defchan
                if current is not None:
                    choices.append( ( current, "Current value: %d" % current ) )
        self.fields['defchan'].choices = choices

    class Meta:
        model   = Mumble
        fields  = ['name', 'display']

    def EXT_authorize( self, request, action ):
        return self.instance.isUserAdmin( request.user )

EXT_FORMS_PROVIDER.register_form( MumbleForm )


class MumbleAdminForm( MumbleForm ):
    """ A Mumble Server admin form intended to be used by the server hoster. """

    users    = forms.IntegerField( required=False )
    usersperchannel     = forms.IntegerField( required=False )
    channelnestinglimit = forms.IntegerField( required=False, help_text=_("Limit channel nesting to this level.") )
    bwidth   = forms.IntegerField( required=False )
    sslca    = forms.CharField( required=False, widget=forms.Textarea, help_text=_("Can be a path or the file content in PEM format.") )
    sslcrt   = forms.CharField( required=False, widget=forms.Textarea )
    sslkey   = forms.CharField( required=False, widget=forms.Textarea )
    sslpassphrase       = forms.CharField( required=False, help_text=_("Passphrase of the SSL Key file, if any.") )
    booted   = forms.BooleanField( required=False, initial=True )
    autoboot = forms.BooleanField( required=False, initial=True )
    bonjour  = forms.BooleanField( required=False )


    class Meta:
        fields  = None
        exclude = None

    def clean_port( self ):
        """ Check if the port number is valid. """

        port = self.cleaned_data['port']

        if port is not None and port != '':
            if port < 1 or port >= 2**16:
                raise forms.ValidationError(
                    _("Port number %(portno)d is not within the allowed range %(minrange)d - %(maxrange)d") % {
                    'portno':   port,
                    'minrange': 1,
                    'maxrange': 2**16,
                    })
            return port
        return None


class MumbleServerForm( ModelForm ):
    defaultconf = forms.CharField( label=_("Default config"), required=False, widget=forms.Textarea )

    def __init__( self, *args, **kwargs ):
        ModelForm.__init__( self, *args, **kwargs )

        # self.instance = instance of MumbleServer, NOT a server instance
        if self.instance and self.instance.id:
            if self.instance.online:
                confstr = ""
                conf = self.instance.defaultconf
                for field in conf:
                    confstr += "%s: %s\n" % ( field, conf[field] )
                self.fields["defaultconf"].initial = confstr
            else:
                self.fields["defaultconf"].initial = _("This server is currently offline.")

    class Meta:
        model = MumbleServer

class MumbleUserForm( ModelForm ):
    """ The user registration form used to register an account. """

    password = forms.CharField( label=_("Password"), widget=forms.PasswordInput, required=False )

    def __init__( self, *args, **kwargs ):
        ModelForm.__init__( self, *args, **kwargs )
        self.server = None

    def EXT_authorize( self, request, action ):
        if not request.user.is_authenticated():
            return False
        if action == "update" and settings.PROTECTED_MODE and self.instance.id is None:
            # creating new user in protected mode -> need UserPasswordForm
            return False
        if self.instance.id is not None and request.user != self.instance.owner:
            # editing another account
            return False
        return True

    def EXT_validate( self, request ):
        self.instance.owner = request.user
        if "serverid" in request.POST:
            try:
                self.server = Mumble.objects.get( id=int(request.POST['serverid']) )
            except Mumble.DoesNotExist:
                return False
            else:
                return True
        return False

    def clean_name( self ):
        """ Check if the desired name is forbidden or taken. """

        name = self.cleaned_data['name']

        if self.server is None:
            raise AttributeError( "You need to set the form's server attribute to the server instance "
                "for validation to work." )

        if self.server.player and re.compile( self.server.player ).match( name ) is None:
            raise forms.ValidationError( _( "That name is forbidden by the server." ) )

        if not self.instance.id and len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) > 0:
            raise forms.ValidationError( _( "Another player already registered that name." ) )

        return name

    def clean_password( self ):
        """ Verify a password has been given. """
        passwd = self.cleaned_data['password']
        if not passwd and ( not self.instance or self.instance.mumbleid == -1 ):
            raise forms.ValidationError( _( "Cannot register player without a password!" ) )
        return passwd

    def save(self):
        self.instance.server = self.server
        ModelForm.save(self)

    class Meta:
        model   = MumbleUser
        fields  = ( 'name', 'password' )

EXT_FORMS_PROVIDER.register_form( MumbleUserForm )


class MumbleUserPasswordForm( MumbleUserForm ):
    """ The user registration form used to register an account on a private server in protected mode. """

    serverpw = forms.CharField(
        label=_('Server Password'),
        help_text=_('This server is private and protected mode is active. Please enter the server password.'),
        widget=forms.PasswordInput(render_value=False)
        )

    def EXT_authorize( self, request, action ):
        if not request.user.is_authenticated():
            return False
        if self.instance.id is not None and request.user != self.instance.owner:
            # editing another account
            return False
        return True

    def clean_serverpw( self ):
        """ Validate the password """
        serverpw = self.cleaned_data['serverpw']
        if self.server.passwd != serverpw:
            raise forms.ValidationError( _( "The password you entered is incorrect." ) )
        return serverpw

    def clean( self ):
        """ prevent save() from trying to store the password in the Model instance. """
        # clean() will be called after clean_serverpw(), so it has already been validated here.
        if 'serverpw' in self.cleaned_data:
            del( self.cleaned_data['serverpw'] )
        return self.cleaned_data

EXT_FORMS_PROVIDER.register_form( MumbleUserPasswordForm )


class MumbleUserLinkForm( MumbleUserForm ):
    """ Special registration form to either register or link an account. """

    linkacc = forms.BooleanField(
        label=_('Link account'),
        help_text=_('The account already exists and belongs to me, just link it instead of creating.'),
        required=False,
        )

    def __init__( self, *args, **kwargs ):
        MumbleUserForm.__init__( self, *args, **kwargs )
        self.mumbleid = None

    def EXT_authorize( self, request, action ):
        if not request.user.is_authenticated() or action == "get":
            return False
        if self.instance.id is not None and request.user != self.instance.owner:
            # editing another account
            return False
        return settings.ALLOW_ACCOUNT_LINKING

    def clean_name( self ):
        """ Check if the target account exists in Murmur. """
        if 'linkacc' not in self.data:
            return MumbleUserForm.clean_name( self )

        # Check if user exists
        name = self.cleaned_data['name']

        if len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) != 1:
            raise forms.ValidationError( _( "No such user found." ) )

        return name

    def clean_password( self ):
        """ Verify that the password is correct. """
        if 'linkacc' not in self.data:
            return MumbleUserForm.clean_password( self )

        if 'name' not in self.cleaned_data:
            # keep clean() from trying to find a user that CAN'T exist
            self.mumbleid = -10
            return ''

        # Validate password with Murmur
        passwd = self.cleaned_data['password']

        self.mumbleid = self.server.ctl.verifyPassword( self.server.srvid, self.cleaned_data['name'], passwd )
        if self.mumbleid <= 0:
            raise forms.ValidationError( _( "The password you entered is incorrect." ) )

        return passwd

    def clean( self ):
        """ Create the MumbleUser instance to save in. """
        if 'linkacc' not in self.data or self.mumbleid <= 0:
            return self.cleaned_data

        # Store the owner that EXT_validate told us
        owner = self.instance.owner

        # try to find a MumbleUser instance for the target user, if none create it
        try:
            m_user = MumbleUser.objects.get( server=self.server, mumbleid=self.mumbleid )
        except MumbleUser.DoesNotExist:
            m_user = MumbleUser( server=self.server, name=self.cleaned_data['name'], mumbleid=self.mumbleid )
            m_user.save( dontConfigureMurmur=True )
        else:
            if m_user.owner is not None:
                raise forms.ValidationError( _( "That account belongs to someone else." ) )

        if m_user.getAdmin() and not settings.ALLOW_ACCOUNT_LINKING_ADMINS:
            raise forms.ValidationError( _( "Linking Admin accounts is not allowed." ) )

        # replace our instance with the mumbleuser found above and reinstate the owner
        self.instance = m_user
        self.instance.owner = owner

        return self.cleaned_data

EXT_FORMS_PROVIDER.register_form( MumbleUserLinkForm )


class MumbleUserAdminForm( PropertyModelForm ):
    aclAdmin = forms.BooleanField( required=False )
    password = forms.CharField( widget=forms.PasswordInput, required=False )

    def clean_password( self ):
        """ Verify a password has been given. """
        passwd = self.cleaned_data['password']
        if not passwd and ( not self.instance or self.instance.mumbleid == -1 ):
            raise forms.ValidationError( _( "Cannot register player without a password!" ) )
        return passwd

    class Meta:
        model   = MumbleUser


class MumbleKickForm( Form ):
    session = forms.IntegerField()
    ban    = forms.BooleanField( required=False )
    reason    = forms.CharField( required=False )


class MumbleTextureForm( Form ):
    """ The form used to upload a new image to be set as texture. """
    usegravatar = forms.BooleanField( required=False, label=_("Use my Gravatar as my Texture") )
    texturefile = forms.ImageField(   required=False, label=_("User Texture") )


