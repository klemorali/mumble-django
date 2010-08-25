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
import datetime
from time      import time
from sys       import stderr
from urllib    import urlopen
from StringIO  import StringIO
from PIL       import Image

from django.utils.translation   import ugettext_noop, ugettext_lazy as _
from django.contrib.auth.models import User
from django.db                  import models
from django.db.models           import signals
from django.conf                import settings

from mumble.mmobjects import mmChannel, mmPlayer
from mumble.mctl      import MumbleCtlBase


def mk_config_property( field, doc="", get_coerce=None, get_none=None, set_coerce=unicode, set_none='' ):
    """ Create a property for the given config field. """

    def get_field( self ):
        if self.id is not None:
            val = self.getConf( field )
            if val is None or val == '':
                return get_none
            if callable(get_coerce):
                return get_coerce( val )
            return val
        return None

    def set_field( self, value ):
        if value is None:
            self.setConf( field, set_none )
        elif callable(set_coerce):
            self.setConf( field, set_coerce(value) )
        else:
            self.setConf( field, value )

    return property( get_field, set_field, doc=doc )

def mk_config_bool_property( field, doc="" ):
    return mk_config_property( field, doc=doc,
        get_coerce = lambda value: value == "true",
        set_coerce = lambda value: str(value).lower()
        )


class MumbleServer( models.Model ):
    """ Represents a Murmur server installation. """

    dbus    = models.CharField( _('DBus or ICE base'), max_length=200, unique=True, default=settings.DEFAULT_CONN, help_text=_(
            "Examples: 'net.sourceforge.mumble.murmur' for DBus or 'Meta:tcp -h 127.0.0.1 -p 6502' for Ice.") )
    secret  = models.CharField( _('Ice Secret'),       max_length=200, blank=True )

    class Meta:
        verbose_name        = _('Mumble Server')
        verbose_name_plural = _('Mumble Servers')

    def __init__( self, *args, **kwargs ):
        models.Model.__init__( self, *args, **kwargs )
        self._ctl  = None
        self._conf = None
        self._version = None

    def __unicode__( self ):
        return self.dbus

    # Ctl instantiation
    def getCtl( self ):
        """ Instantiate and return a MumbleCtl object for this server.

            Only one instance will be created, and reused on subsequent calls.
        """
        if not self._ctl:
            self._ctl = MumbleCtlBase.newInstance( self.dbus, settings.SLICE, self.secret )
        return self._ctl

    ctl = property( getCtl, doc="Get a Control object for this server. The ctl is cached for later reuse." )

    def isMethodDbus(self):
        """ Return true if this instance uses DBus. """
        rd = re.compile( r'^(\w+\.)*\w+$' )
        return bool(rd.match(self.dbus))

    method_dbus = property( isMethodDbus )
    method_ice  = property( lambda self: not self.isMethodDbus(), doc="Return true if this instance uses Ice." )

    def getDefaultConf( self, field=None ):
        """ Get a field from the default conf dictionary, or None if the field isn't set. """
        if self._conf is None:
            self._conf = self.ctl.getDefaultConf()
        if field is None:
            return self._conf
        if field in self._conf:
            return self._conf[field]
        return None

    def isOnline( self ):
        """ Return true if this server process is running. """
        possibleexceptions = []
        try:
            from Ice import ConnectionRefusedException
        except ImportError, err:
            if self.method_ice:
                print >> stderr, err
                return None
        else:
            possibleexceptions.append( ConnectionRefusedException )
        try:
            from dbus import DBusException
        except ImportError, err:
            if self.method_dbus:
                print >> stderr, err
                return None
        else:
            possibleexceptions.append( DBusException )

        try:
            self.ctl
        except tuple(possibleexceptions), err:
            print >> stderr, err
            return False
        except (EnvironmentError, RuntimeError), err:
            print >> stderr, err
            return None
        else:
            return True

    online = property( isOnline )
    defaultconf = property( getDefaultConf, doc="The default config dictionary." )

    def getDefaultPort( self ):
        """ Return the default port configured on this server. """
        if "port" in self.defaultconf:
            return int(self.defaultconf['port'])
        else:
            return settings.MUMBLE_DEFAULT_PORT

    defaultPort = property( getDefaultPort )

    def getVersion( self ):
        """ Return the version of Murmur. """
        if self._version is None:
            self._version = self.ctl.getVersion()
        return self._version

    version = property( getVersion )

    prettyversion = property( lambda self: '.'.join( map( str, self.version[:3] ) ),
        doc="Pretty-Printed version" )


class Mumble( models.Model ):
    """ Represents a Murmur server instance.

        All configurable settings are represented by a field in this model. To change the
        settings, just update the appropriate field and call the save() method.

        To set up a new server instance, instanciate this Model. The first field you should
        define is the "dbus" field, which tells the connector subsystem how to connect to
        the Murmurd master process. Set this to the appropriate DBus service name or the
        Ice proxy string.

        When an instance of this model is deleted, the according server instance will be
        deleted as well.
    """

    server  = models.ForeignKey(   MumbleServer, verbose_name=_("Mumble Server") )
    name    = models.CharField(    _('Server Name'),            max_length=200 )
    srvid   = models.IntegerField( _('Server ID'),              editable=False )
    addr    = models.CharField(    _('Server Address'),         max_length=200, blank=True, help_text=_(
            "Hostname or IP address to bind to. You should use a hostname here, because it will appear on the "
            "global server list.") )
    port    = models.IntegerField( _('Server Port'),            blank=True, null=True, help_text=_(
            "Port number to bind to. Leave empty to auto assign one.") )
    display = models.CharField(    _('Server Display Address'), max_length=200, blank=True, help_text=_(
            "This field is only relevant if you are located behind a NAT, and names the Hostname or IP address "
            "to use in the Channel Viewer and for the global server list registration. If not given, the addr "
            "and port fields are used. If display and bind ports are equal, you can omit it here.") )

    supw    = property( lambda self: '',
            lambda self, value: ( value and self.ctl.setSuperUserPassword( self.srvid, value ) ) or None,
            doc=_('Superuser Password')
            )

    url     = mk_config_property( "registerurl",            ugettext_noop("Website URL") )
    motd    = mk_config_property( "welcometext",            ugettext_noop("Welcome Message") )
    passwd  = mk_config_property( "password",               ugettext_noop("Server Password") )
    users   = mk_config_property( "users",                  ugettext_noop("Max. Users"),         get_coerce=int )
    bwidth  = mk_config_property( "bandwidth",              ugettext_noop("Bandwidth [Bps]"),    get_coerce=int )
    sslcrt  = mk_config_property( "certificate",            ugettext_noop("SSL Certificate") )
    sslkey  = mk_config_property( "key",                    ugettext_noop("SSL Key") )
    player  = mk_config_property( "username",               ugettext_noop("Player name regex") )
    channel = mk_config_property( "channelname",            ugettext_noop("Channel name regex") )
    defchan = mk_config_property( "defaultchannel",         ugettext_noop("Default channel"),    get_coerce=int )
    timeout = mk_config_property( "timeout",                ugettext_noop("Timeout"),            get_coerce=int )
    textlen = mk_config_property( "textmessagelength",      ugettext_noop("Maximum length of text messages") )
    usersperchannel = mk_config_property( "usersperchannel",ugettext_noop("Users per channel"),  get_coerce=int )

    obfsc   = mk_config_bool_property( "obfuscate",         ugettext_noop("IP Obfuscation") )
    certreq = mk_config_bool_property( "certrequired",      ugettext_noop("Require Certificate") )
    html    = mk_config_bool_property( "allowhtml",         ugettext_noop("Allow HTML to be used in messages") )
    bonjour = mk_config_bool_property( "bonjour",           ugettext_noop("Publish this server via Bonjour") )
    autoboot= mk_config_bool_property( "boot",              ugettext_noop("Boot Server when Murmur starts") )

    def get_absolute_url( self ):
        from views import show
        from django.core.urlresolvers import reverse
        return reverse( show, kwargs={ 'server': self.id } )

    def getBooted( self ):
        if self.id is not None:
            if self.server.online:
                return self.ctl.isBooted( self.srvid )
            else:
                return None
        else:
            return False

    def setBooted( self, value ):
        if value != self.getBooted():
            if value:
                self.ctl.start( self.srvid )
            else:
                self.ctl.stop( self.srvid )

    booted  = property( getBooted, setBooted, doc=ugettext_noop("Boot Server") )
    online  = property( getBooted, setBooted, doc=ugettext_noop("Boot Server") )

    defaultPort = property( lambda self: self.server.defaultPort + self.srvid - 1,
        doc="Default port for this server instance" )
    boundPort   = property( lambda self: self.port or self.defaultPort,
        doc="The port that this instance actually binds to" )

    class Meta:
        unique_together     = ( ( 'server', 'srvid' ), )
        verbose_name        = _('Server instance')
        verbose_name_plural = _('Server instances')

    def __unicode__( self ):
        if not self.id:
            return u'Murmur "%s" (NOT YET CREATED)' % self.name
        return u'Murmur "%s" (%d)' % ( self.name, self.srvid )

    def save( self, dontConfigureMurmur=False, *args, **kwargs ):
        """ Save the options configured in this model instance not only to Django's database,
            but to Murmur as well.
        """
        if dontConfigureMurmur:
            return models.Model.save( self, *args, **kwargs )

        if self.id is None:
            self.srvid = self.ctl.newServer()

        self.ctl.setConf( self.srvid, 'registername', self.name )

        if self.addr:
            self.ctl.setConf( self.srvid, 'host', self.addr )
        else:
            self.ctl.setConf( self.srvid, 'host', '' )

        if self.port and self.port != self.defaultPort:
            self.ctl.setConf( self.srvid, 'port', str(self.port) )
        else:
            self.ctl.setConf( self.srvid, 'port', '' )

        if self.netloc:
            self.ctl.setConf( self.srvid, 'registerhostname', self.netloc )
        else:
            self.ctl.setConf( self.srvid, 'registerhostname', '' )

        return models.Model.save( self, *args, **kwargs )


    def __init__( self, *args, **kwargs ):
        models.Model.__init__( self, *args, **kwargs )
        self._channels = None
        self._rootchan = None


    users_regged = property( lambda self: self.mumbleuser_set.count(),           doc="Number of registered users." )
    users_online = property( lambda self: len(self.ctl.getPlayers(self.srvid)),  doc="Number of online users." )
    channel_cnt  = property( lambda self: len(self.ctl.getChannels(self.srvid)), doc="Number of channels." )
    is_public    = property( lambda self: not self.passwd,
                             doc="False if a password is needed to join this server." )
    uptime       = property( lambda self: self.ctl.getUptime(self.srvid),
                             doc="Number of seconds this instance has been running." )
    upsince      = property( lambda self: datetime.datetime.fromtimestamp( float( time() - self.uptime ) ),
                             doc="Datetime since when the server is running." )

    is_server  = True
    is_channel = False
    is_player  = False

    ctl = property( lambda self: self.server.ctl )

    def getBans( self ):
        return self.ctl.getBans( self.srvid )

    def getConf( self, field ):
        return self.ctl.getConf( self.srvid, field )

    def setConf( self, field, value ):
        return self.ctl.setConf( self.srvid, field, value )

    def configureFromMurmur( self ):
        conf = self.ctl.getAllConf( self.srvid )

        if "registername" not in conf or not conf["registername"]:
            self.name = "noname"
        else:
            self.name = conf["registername"]

        if "host" in conf:
            self.addr = conf["host"]
        else:
            self.addr = ""

        if "port" in conf:
            self.port = int(conf["port"])
        else:
            self.port = None

        if "registerhostname" in conf and conf["registerhostname"] != self.addr:
            self.display = conf["registerhostname"]
            if ' ' in self.addr and self.display == self.addr.split(' ')[0]:
                self.display = ""
        else:
            self.display = ""

        self.save( dontConfigureMurmur=True )


    def readUsersFromMurmur( self, verbose=0 ):
        if not self.booted:
            raise SystemError( "This murmur instance is not currently running, can't sync." )

        players = self.ctl.getRegisteredPlayers(self.srvid)
        known_ids = [rec["mumbleid"]
            for rec in MumbleUser.objects.filter( server=self ).values( "mumbleid" )
            ]

        for idx in players:
            playerdata = players[idx]

            if playerdata.userid == 0: # Skip SuperUsers
                continue
            if verbose > 1:
                print "Checking Player with id %d." % playerdata.userid

            if playerdata.userid not in known_ids:
                if verbose:
                    print 'Found new Player "%s".' % playerdata.name

                playerinstance = MumbleUser(
                    mumbleid = playerdata.userid,
                    name     = playerdata.name,
                    password = '',
                    server   = self,
                    owner    = None
                    )

            else:
                if verbose > 1:
                    print "Player '%s' is already known." % playerdata.name
                playerinstance = MumbleUser.objects.get( server=self, mumbleid=playerdata.userid )
                playerinstance.name = playerdata.name

            playerinstance.save( dontConfigureMurmur=True )


    def isUserAdmin( self, user ):
        """ Determine if the given user is an admin on this server. """
        if user.is_authenticated():
            if user.is_superuser:
                return True
            try:
                return self.mumbleuser_set.get( owner=user ).getAdmin()
            except MumbleUser.DoesNotExist:
                return False
        return False


    # Deletion handler
    def deleteServer( self ):
        """ Delete this server instance from Murmur. """
        self.ctl.deleteServer(self.srvid)

    @staticmethod
    def pre_delete_listener( **kwargs ):
        kwargs['instance'].deleteServer()


    # Channel list
    def getChannels( self ):
        """ Query the channels from Murmur and create a tree structure.

            Again, this will only be done for the first call to this function. Subsequent
            calls will simply return the list created last time.
        """
        if self._channels is None:
            self._channels = {}
            chanlist = self.ctl.getChannels(self.srvid).values()
            links = {}

            # sometimes, ICE seems to return the Channel list in a weird order.
            # itercount prevents infinite loops.
            itercount = 0
            maxiter   = len(chanlist) * 3
            while len(chanlist) and itercount < maxiter:
                itercount += 1
                for theChan in chanlist:
                    # Channels - Fields: 0 = ID, 1 = Name, 2 = Parent-ID, 3 = Links
                    if( theChan.parent == -1 ):
                        # No parent
                        self._channels[theChan.id] = mmChannel( self, theChan )
                    elif theChan.parent in self.channels:
                        # parent already known
                        self._channels[theChan.id] = mmChannel( self, theChan, self.channels[theChan.parent] )
                    else:
                        continue

                    chanlist.remove( theChan )

                    self._channels[theChan.id].serverId = self.id

                    # process links - if the linked channels are known, link; else save their ids to link later
                    for linked in theChan.links:
                        if linked in self._channels:
                            self._channels[theChan.id].linked.append( self._channels[linked] )
                        else:
                            if linked not in links:
                                links[linked] = list()
                            links[linked].append( self._channels[theChan.id] )

                    # check if earlier round trips saved channel ids to be linked to the current channel
                    if theChan.id in links:
                        for targetChan in links[theChan.id]:
                            targetChan.linked.append( self._channels[theChan.id] )

            self._channels[0].name = self.name

            self.players = {}
            for thePlayer in self.ctl.getPlayers(self.srvid).values():
                # Players - Fields: 0 = UserID, 6 = ChannelID
                self.players[ thePlayer.session ] = mmPlayer( self, thePlayer, self._channels[ thePlayer.channel ] )

            self._channels[0].sort()

        return self._channels

    channels = property( getChannels,                       doc="A convenience wrapper for getChannels()."    )
    rootchan = property( lambda self: self.channels[0],     doc="A convenience wrapper for getChannels()[0]." )

    def getNetloc( self ):
        """ Return the address from the Display field (if any), or the server address.
            Users from outside a NAT will need to use the Display address to connect
            to this server instance.
        """
        if self.display:
            # Find out if this is a sensible address *with port*.
            # Regex checks for (hostname OR [ipv6] OR ipv4):port.
            if re.match( r'^([^:]+|\[[\da-fA-F]{0,4}(:[\da-fA-F]{0,4})+\]|\d{1,3}(\.\d{1,3}){3}):\d{1,5}$', self.display):
                return self.display
            else:
                daddr = self.display
        elif " " in self.addr:
            # If Murmur binds to multiple addresses, use the first
            daddr = self.addr.split(" ")[0]
        else:
            daddr = self.addr

        if ":" in daddr:
            # []-escape IPv6 addresses
            daddr = "[%s]" % daddr

        if self.boundPort != settings.MUMBLE_DEFAULT_PORT:
            return "%s:%d" % (daddr, self.boundPort)
        else:
            return daddr

    netloc = property( getNetloc )

    def getURL( self, forUser = None ):
        """ Create an URL of the form mumble://username@host:port/ for this server. """
        if not self.netloc:
            return None
        from urlparse import urlunsplit
        versionstr = "version=%s" % self.prettyversion
        if forUser is not None:
            netloc = "%s@%s" % ( forUser.name, self.netloc )
            return urlunsplit(( "mumble", netloc, "", versionstr, "" ))
        else:
            return urlunsplit(( "mumble", self.netloc, "", versionstr, "" ))

    connecturl = property( getURL )

    version = property( lambda self: self.server.version, doc="The version of Murmur." )
    prettyversion = property( lambda self: self.server.prettyversion )

    def asDict( self, authed=False ):
        return { 'name':   self.name,
             'id':     self.id,
             'root':   self.rootchan.asDict( authed ),
             'x_connecturl': self.connecturl,
             'x_uptime': self.uptime,
            }

    def asXml( self, authed=False ):
        from xml.etree.cElementTree import Element
        root = Element( "server",
            xmlns="http://mumble.sourceforge.net/Channel_Viewer_Protocol",
            id=unicode(self.id), name=self.name
            )
        root.set( 'x_connecturl', self.connecturl )
        root.set( 'x_uptime', unicode(self.uptime) )
        root.set( 'xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance" )
        root.set( 'xsi:schemaLocation',
            "http://bitbucket.org/Svedrin/mumble-django/wiki/channel-viewer-protocol_murmur-%d-%d-%d.xsd" % self.version[:3]
            )

        self.rootchan.asXml( root, authed )
        return root

    def asMvXml( self ):
        """ Return an XML tree for this server suitable for MumbleViewer-ng. """
        from xml.etree.cElementTree import Element
        root = Element("root")
        self.rootchan.asMvXml(root)
        return root

    def asMvJson( self ):
        """ Return a Dict for this server suitable for MumbleViewer-ng. """
        return self.rootchan.asMvJson()

    # "server" field protection
    def __setattr__( self, name, value ):
        if name == 'server':
            if self.id is not None and self.server != value:
                raise AttributeError( _( "This field must not be updated once the record has been saved." ) )

        models.Model.__setattr__( self, name, value )

    def kickUser( self, sessionid, reason="" ):
        return self.ctl.kickUser( self.srvid, sessionid, reason )

    def banUser( self, sessionid, reason="", duration=0 ):
        return self.ctl.addBanForSession( self.srvid, sessionid, reason=reason, duration=duration )

    def moveUser( self, sessionid, channelid ):
        return self.ctl.moveUser( self.srvid, sessionid, channelid )

    def muteUser( self, sessionid, mute=True ):
        return self.ctl.muteUser( self.srvid, sessionid, mute )

    def deafenUser( self, sessionid, deafen=True ):
        return self.ctl.deafenUser( self.srvid, sessionid, deafen )

    def hasUserTexture( self, userid ):
        """ Check if this user has a texture set. """
        if userid == -1:
            return False
        try:
            self.getUserTexture( userid )
        except ValueError:
            return False
        else:
            return True

    def getUserTexture( self, userid ):
        return self.ctl.getTexture( self.srvid, userid )

    def setUserTexture( self, userid, image ):
        return self.ctl.setTexture( self.srvid, userid, image )

    def addChannel( self, name, parentid ):
        return self.ctl.addChannel( self.srvid, name, parentid )

    def removeChannel( self, channelid ):
        return self.ctl.removeChannel( self.srvid, channelid )

    def renameChannel( self, channelid, name, description ):
        return self.ctl.renameChannel( self.srvid, channelid, name, description )

    def moveChannel( self, channelid, parentid ):
        return self.ctl.moveChannel( self.srvid, channelid, parentid )

    def getLog( self, first=0, last=100, filter="" ):
        """ Return log entries from ``first`` to ``last`` that contain ``filter`` (if any). """
        logentries = self.ctl.getLog( self.srvid, first, last )
        if not filter:
            return logentries
        return [ logentry for logentry in logentries if filter in logentry.txt ]


def mk_registration_property( field, doc="" ):
    """ Create a property for the given registration field. """

    def get_field( self ):
        if field in self.registration:
            return self.registration[field]
        else:
            return None

    return property( get_field, doc=doc )


class MumbleUser( models.Model ):
    """ Represents a User account in Murmur.

        To change an account, simply set the according field in this model and call the save()
        method to update the account in Murmur and in Django's database. Note that, once saved
        for the first time, the server field must not be changed. Attempting to do this will
        result in an AttributeError. To move an account to a new server, recreate it on the
        new server and delete the old model.

        When you delete an instance of this model, the according user account will be deleted
        in Murmur as well, after revoking the user's admin privileges.
    """

    mumbleid = models.IntegerField(         _('Mumble player_id'),             editable = False, default = -1 )
    name     = models.CharField(            _('User name and Login'),          max_length = 200 )
    password = models.CharField(            _('Login password'),               max_length = 200, blank=True )
    server   = models.ForeignKey(   Mumble, verbose_name=_('Server instance'), related_name="mumbleuser_set" )
    owner    = models.ForeignKey(   User,   verbose_name=_('Account owner'),   related_name="mumbleuser_set", null=True, blank=True )

    comment = mk_registration_property( "comment", doc=ugettext_noop("The user's comment.") )
    hash    = mk_registration_property( "hash",    doc=ugettext_noop("The user's hash.")    )

    gravatar256 = property( lambda self: self.gravatarUrl( size=256 ) )
    gravatar128 = property( lambda self: self.gravatarUrl( size=128 ) )
    gravatar64  = property( lambda self: self.gravatarUrl( size=64  ) )
    gravatar    = property( lambda self: self.gravatarUrl() )

    class Meta:
        unique_together     = ( ( 'server', 'owner' ), ( 'server', 'mumbleid' ) )
        verbose_name        = _( 'User account'  )
        verbose_name_plural = _( 'User accounts' )

    is_server  = False
    is_channel = False
    is_player  = True

    def __unicode__( self ):
        return _("Mumble user %(mu)s on %(srv)s owned by Django user %(du)s") % {
            'mu':  self.name,
            'srv': self.server,
            'du':  self.owner
            }

    def save( self, dontConfigureMurmur=False, *args, **kwargs ):
        """ Save the settings in this model to Murmur. """
        if dontConfigureMurmur:
            return models.Model.save( self, *args, **kwargs )

        ctl = self.server.ctl

        if self.owner:
            email = self.owner.email
        else:
            email = settings.DEFAULT_FROM_EMAIL

        if self.id is None:
            # This is a new user record, so Murmur doesn't know about it yet
            if len( ctl.getRegisteredPlayers( self.server.srvid, self.name ) ) > 0:
                raise ValueError( _( "Another player already registered that name." ) )
            if not self.password:
                raise ValueError( _( "Cannot register player without a password!" ) )

            self.mumbleid = ctl.registerPlayer( self.server.srvid, self.name, email, self.password )

        # Update user's registration
        elif self.password:
            ctl.setRegistration(
                self.server.srvid,
                self.mumbleid,
                self.name,
                email,
                self.password
                )

        # Don't save the users' passwords, we don't need them anyway
        self.password = ''

        # If enabled (and possible), set Gravatar as default Avatar
        if not self.hasTexture and settings.USE_GRAVATAR and self.gravatar:
            self.setTextureFromUrl( self.gravatar )

        return models.Model.save( self, *args, **kwargs )

    def __init__( self, *args, **kwargs ):
        models.Model.__init__( self, *args, **kwargs )
        self._registration = None

    # Admin handlers
    def getAdmin( self ):
        """ Get ACL of root Channel, get the admin group and see if this user is in it. """
        if self.mumbleid == -1:
            return False
        else:
            return self.server.rootchan.acl.group_has_member( "admin", self.mumbleid )

    def setAdmin( self, value ):
        """ Set or revoke this user's membership in the admin group on the root channel. """
        if self.mumbleid == -1:
            return False
        if value:
            self.server.rootchan.acl.group_add_member( "admin", self.mumbleid )
        else:
            self.server.rootchan.acl.group_remove_member( "admin", self.mumbleid )
        self.server.rootchan.acl.save()
        return value

    aclAdmin = property( getAdmin, setAdmin, doc=ugettext_noop('Admin on root channel') )


    # Registration fetching
    def getRegistration( self ):
        """ Retrieve a user's registration from Murmur as a dict. """
        if not self._registration:
            self._registration = self.server.ctl.getRegistration( self.server.srvid, self.mumbleid )
        return self._registration

    registration = property( getRegistration )

    # Texture handlers
    def getTexture( self ):
        """ Get the user texture as a PIL Image. """
        return self.server.getUserTexture( self.mumbleid )

    def setTexture( self, image ):
        """ Install the given image as the user's texture. """
        self.server.setTexture( self.mumbleid, image )

    def setTextureFromUrl( self, url, transparency=None ):
        """ Retrieve the image at the given URL and set it as my texture. """
        img = Image.open( StringIO( urlopen( url ).read() ) )
        self.setTexture( img )

    texture = property( getTexture, setTexture,
        doc="Get the texture as a PIL Image or set the Image as the texture."
        )

    def hasTexture( self ):
        """ Check if this user has a texture set. """
        return self.server.hasUserTexture( self.mumbleid )

    def gravatarUrl( self, size=80 ):
        """ Get a Gravatar URL for my owner's email adress (if any), or using the User's cert hash.
            The size parameter is optional, and defaults to 80 pixels (the default used by Gravatar
            if you omit this parameter in the URL).
        """
        if self.owner and self.owner.email:
            from hashlib import md5
            return settings.GRAVATAR_URL % { 'hash': md5(self.owner.email).hexdigest(), 'size': size }
        elif self.hash:
            return settings.GRAVATAR_URL % { 'hash': self.hash, 'size': size }
        return None

    def getTextureUrl( self ):
        """ Get a URL under which the texture can be retrieved. """
        from views                import showTexture
        from django.core.urlresolvers        import reverse
        return reverse( showTexture, kwargs={ 'server': self.server.id, 'userid': self.id } )

    textureUrl = property( getTextureUrl )


    # Deletion handler
    @staticmethod
    def pre_delete_listener( **kwargs ):
        kwargs['instance'].unregister()

    def unregister( self ):
        """ Delete this user account from Murmur. """
        if self.getAdmin():
            self.setAdmin( False )
        self.server.ctl.unregisterPlayer(self.server.srvid, self.mumbleid)


    # "server" field protection
    def __setattr__( self, name, value ):
        if name == 'server':
            if self.id is not None and self.server != value:
                raise AttributeError( _( "This field must not be updated once the record has been saved." ) )

        models.Model.__setattr__( self, name, value )




signals.pre_delete.connect( Mumble.pre_delete_listener,     sender=Mumble     )
signals.pre_delete.connect( MumbleUser.pre_delete_listener, sender=MumbleUser )




