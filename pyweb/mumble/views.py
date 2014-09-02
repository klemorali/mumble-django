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

import json
import re

from StringIO     import StringIO
from PIL          import Image

from django.shortcuts               import render_to_response, get_object_or_404, get_list_or_404
from django.template                import RequestContext
from django.http                    import Http404, HttpResponse, HttpResponseRedirect
from django.conf                    import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models     import User
from django.contrib.auth            import views as auth_views
from django.core.urlresolvers       import reverse
from django.views.decorators.csrf   import csrf_exempt

from models import Mumble, MumbleUser
from forms  import MumbleForm, MumbleUserForm, MumbleUserPasswordForm
from forms  import MumbleUserLinkForm, MumbleTextureForm, MumbleKickForm
from utils  import iptostring

from djextdirect.provider import Provider
from djextdirect.views    import login, logout

EXT_DIRECT_PROVIDER = Provider()

EXT_DIRECT_PROVIDER._register_method( "Accounts", login  )
EXT_DIRECT_PROVIDER._register_method( "Accounts", logout )


def validate_jsonp_callback(callback):
    if not re.match( "^[a-zA-Z][\w.]+$", callback ):
        raise Http404("Illegal characters in callback")


def redir( request ):
    """ Redirect to the servers list. """
    if 'HTTP_USER_AGENT' in request.META and (
      request.META['HTTP_USER_AGENT'].startswith( 'BlackBerry' ) or \
      "Opera Mobi" in request.META['HTTP_USER_AGENT'] or \
      "Opera Mini" in request.META['HTTP_USER_AGENT'] or \
      "Windows CE" in request.META['HTTP_USER_AGENT'] or \
      "MIDP"       in request.META['HTTP_USER_AGENT'] or \
      "Palm"       in request.META['HTTP_USER_AGENT'] or \
      "NetFront"   in request.META['HTTP_USER_AGENT'] or \
      "Nokia"      in request.META['HTTP_USER_AGENT'] or \
      "Symbian"    in request.META['HTTP_USER_AGENT'] or \
      "UP.Browser" in request.META['HTTP_USER_AGENT'] or \
      "UP.Link"    in request.META['HTTP_USER_AGENT'] or \
      "WinWAP"     in request.META['HTTP_USER_AGENT'] or \
      "Android"    in request.META['HTTP_USER_AGENT'] or \
      "DoCoMo"     in request.META['HTTP_USER_AGENT'] or \
      "KDDI-"      in request.META['HTTP_USER_AGENT'] or \
      "Softbank"   in request.META['HTTP_USER_AGENT'] or \
      "J-Phone"    in request.META['HTTP_USER_AGENT'] or \
      "IEMobile"   in request.META['HTTP_USER_AGENT'] or \
      "iPod"       in request.META['HTTP_USER_AGENT'] or \
      "iPhone"     in request.META['HTTP_USER_AGENT'] ):
        return HttpResponseRedirect( reverse( mobile_mumbles ) )
    else:
        return HttpResponseRedirect( reverse( mumbles ) )


def mobile_mumbles( request ):
    return mumbles( request, mobile=True )


def mumbles( request, mobile=False ):
    """ Display a list of all configured Mumble servers, or redirect if only one configured. """
    mms = Mumble.objects.all().order_by( "name" )
    if settings.HIDE_OFFLINE_SERVERS:
        mms = filter(lambda srv: srv.booted, mms)

    if len(mms) == 1:
        return HttpResponseRedirect( reverse(
            { False: show, True: mobile_show }[mobile],
            kwargs={ 'server': mms[0].id, }
            ) )

    return render_to_response(
        'mumble/%s.html' % { False: 'list', True: 'mobile_list' }[mobile],
        { 'MumbleObjects': mms,
          'MumbleActive':  True,
        },
        context_instance = RequestContext(request)
        )

@EXT_DIRECT_PROVIDER.register_method( "MumbleList" )
def servers( request ):
    mms = Mumble.objects.all().order_by( "name" )
    if settings.HIDE_OFFLINE_SERVERS:
        mms = filter(lambda srv: srv.booted, mms)
    return [{ 'id': mm.id, 'name': mm.name, 'booted': mm.booted } for mm in mms]

@EXT_DIRECT_PROVIDER.register_method( "MumbleList" )
def serverinfo( request, server ):
    srv = Mumble.objects.get( id=int(server) )
    if srv.booted:
        return {
            'id':            srv.id,
            'name':          srv.name,
            'booted':        True,
            'motd':          srv.motd,
            'connecturl':    srv.connecturl,
            'prettyversion': srv.prettyversion,
            'url':           srv.url,
            'users':         (srv.users or srv.server.getDefaultConf()['users']),
            'users_regged':  srv.users_regged,
            'users_online':  srv.users_online,
            'channel_cnt':   srv.channel_cnt,
            'uptime':        srv.uptime,
            'upsince':       unicode(srv.upsince),
            'minurl':        reverse( mobile_show, args=(server,) ),
            'detailsurl':    reverse( show,        args=(server,) ),
            }
    else:
        return{
            'id':            srv.id,
            'name':          srv.name,
            'booted':        False,
            'minurl':        reverse( mobile_show, args=(server,) ),
            'detailsurl':    reverse( show,        args=(server,) ),
            }

def show( request, server ):
    """ Display the channel list for the given Server ID.

        This includes not only the channel list itself, but indeed the user registration,
        server admin and user texture form as well. The template then uses JavaScript
        to display these forms integrated into the Channel viewer.
    """
    srv = get_object_or_404( Mumble, id=server )
    if not srv.booted:
        return render_to_response(
            'mumble/offline.html',
            { 'DBaseObject':  srv,
              'MumbleActive': True,
            }, context_instance = RequestContext(request) )

    isAdmin = srv.isUserAdmin( request.user )
    if request.user.is_authenticated():
        try:
            user = MumbleUser.objects.get( server=srv, owner=request.user )
        except MumbleUser.DoesNotExist:
            user = None
    else:
        user = None

    from mumble.forms import EXT_FORMS_PROVIDER, MumbleUserPasswordForm, MumbleUserLinkForm, MumbleUserForm

    regformname = None
    if not user:
        # Unregistered users may or may not need a password to register.
        if settings.PROTECTED_MODE and srv.passwd:
            regformname = "MumbleUserPasswordForm"
            EXT_FORMS_PROVIDER.register_form( MumbleUserPasswordForm )
        # Unregistered users may or may not want to link an existing account
        elif settings.ALLOW_ACCOUNT_LINKING:
            regformname = "MumbleUserLinkForm"
            EXT_FORMS_PROVIDER.register_form( MumbleUserLinkForm )
    if not regformname:
        regformname = "MumbleUserForm"
        EXT_FORMS_PROVIDER.register_form( MumbleUserForm )

    try:
        import qrencode
    except ImportError:
        qravail = False
    else:
        qravail = True

    return render_to_response( 'mumble/mumble.html', {
            'MumbleServer': srv,
            'ServerDict':   json.dumps(serverinfo(request, server)),
            'RegForm':      regformname,
            'MumbleActive': True,
            'MumbleAccount':user,
            'QRAvailable':  qravail,
            'IsAdmin':      isAdmin,
            'UsersAboveChannels': settings.USERS_ABOVE_CHANNELS
        }, context_instance = RequestContext(request) )

def mobile_show( request, server ):
    """ Display the channel list for the given Server ID. """

    srv = get_object_or_404( Mumble, id=server )

    user = None
    if request.user.is_authenticated():
        try:
            user = MumbleUser.objects.get( server=srv, owner=request.user )
        except MumbleUser.DoesNotExist:
            pass

    return render_to_response( 'mumble/mobile_mumble.html', {
            'DBaseObject':  srv,
            'MumbleActive': True,
            'MumbleAccount':user,
        }, context_instance = RequestContext(request) )

def embed( request, server ):
    """ Display the channel viewer for the given Server ID. """

    srv = get_object_or_404( Mumble, id=server )

    return render_to_response( 'mumble/embed.html', {
            'MumbleServer': srv,
            'MumbleActive': True,
            'UsersAboveChannels': settings.USERS_ABOVE_CHANNELS
        }, context_instance = RequestContext(request) )

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def hasTexture( request, server, userid ):
    srv = get_object_or_404( Mumble,     id=int(server) )
    if srv.hasUserTexture(int(userid)):
        return {
            'has': True,
            'url': reverse( showTexture, kwargs={ 'server': server, 'userid': userid } )
            }
    else:
        return { 'has': False, 'url': None }

def showTexture( request, server, userid ):
    """ Pack the given user's texture into an HttpResponse. """

    srv  = get_object_or_404( Mumble,     id=int(server) )

    try:
        img  = srv.getUserTexture(int(userid))
    except ValueError:
        raise Http404()
    else:
        buf = StringIO()
        img.save( buf, "PNG" )
        return HttpResponse( buf.getvalue(), "image/png" )

def qrcode( request, server ):
    """ Show a QR Coce image that links to the server's embedded page. """

    try:
        import qrencode
    except ImportError:
        return HttpResponse( "oh noez" )
    else:
        from django.contrib.sites.models import Site
        version, size, img = qrencode.encode_scaled( "%s://%s%s" % (
            { False: "http", True: "https" }[request.is_secure()],
            Site.objects.get_current().domain,
            reverse( embed, kwargs={ 'server': server } )
            ), 82 )
        buf = StringIO()
        img.save( buf, "PNG" )
        return HttpResponse( buf.getvalue(), "image/png" )

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def get_admin( request, server ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    adminform = MumbleForm( request.POST, instance=srv )
    data = {}
    for fld in adminform.fields:
        data[fld] = getattr( srv, fld )
    return { 'data': data, 'success': True }

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def log( request, server, start, limit, filter ):
    """ Retrieve log messages. """
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( "Access denied" )
    return { 'data': [
            { 'timestamp': ent.timestamp, 'txt': ent.txt }
            for ent in srv.getLog( start, (start + limit), filter )
        ], 'success': True }

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def bans( request, server ):
    """ Retrieve bans. """
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( "Access denied" )
    return { 'data': [
            { 'start': ent.start, 'address': ent.address, 'bits': ent.bits,
              'duration': ent.duration, 'reason': ent.reason, 'name': ent.name,
              'addrstr': iptostring(ent.address) }
            for ent in srv.getBans()
        ], 'success': True }

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def removeBan( request, server, bandata ):
    """ Retrieve bans. """
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( "Access denied" )
    if "addrstr" in bandata:
        del bandata["addrstr"]
    bandata["address"] = tuple(bandata["address"])
    cleanargs = {}
    for kw in bandata:
        cleanargs[str(kw)] = bandata[kw]
    return srv.removeBan( **cleanargs )


@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def moveUser( request, server, sessionid, channelid ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.moveUser( sessionid, channelid )

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def moveChannel( request, server, channelid, parentid ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.moveChannel( channelid, parentid )

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def kickUser( request, server, sessionid, reason, ban, duration ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    if ban:
        srv.banUser( sessionid, reason, duration )
    srv.kickUser( sessionid, reason )

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def muteUser( request, server, sessionid, mute ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.muteUser(sessionid, mute)

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def deafenUser( request, server, sessionid, deaf ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.deafenUser(sessionid, deaf)

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def addChannel( request, server, name, parentid ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.addChannel(name, parentid)

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def removeChannel( request, server, channelid ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.removeChannel(channelid)

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def renameChannel( request, server, channelid, name, description ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.renameChannel(channelid, name, description)

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def sendMessage( request, server, sessionid, message ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.sendMessage(sessionid, message)

@EXT_DIRECT_PROVIDER.register_method( "Mumble" )
def sendMessageChannel( request, server, channelid, tree, message ):
    srv = get_object_or_404( Mumble, id=int(server) )
    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )
    srv.sendMessageChannel(channelid, tree, message)

@EXT_DIRECT_PROVIDER.register_method( "MumbleUserAdmin" )
def users( request, server, resync=False ):
    """ Create a list of MumbleUsers for a given server serialized as a JSON object.

        If the request has a "data" field, evaluate that and update the user records.
    """

    srv = get_object_or_404( Mumble, id=int(server) )

    if resync:
        srv.readUsersFromMurmur()

    if not srv.isUserAdmin( request.user ):
        raise Exception( 'Access denied' )

    users = []
    for mu in srv.mumbleuser_set.all():
        owner = None
        if mu.owner is not None:
            owner = mu.owner.id

        users.append( {
            'id':       mu.id,
            'name':     mu.name,
            'password': None,
            'owner':    owner,
            'admin':    mu.aclAdmin,
            } )

    return users

@EXT_DIRECT_PROVIDER.register_method( "MumbleUserAdmin" )
def djangousers( request ):
    """ Return a list of all Django users' names and IDs. """

    users = [ { 'uid': '', 'uname': '------' } ]
    for du in User.objects.all().order_by( 'username' ):
        users.append( {
            'uid':   du.id,
            'uname': unicode( du ),
            } )

    return users

@EXT_DIRECT_PROVIDER.register_method( "MumbleUserAdmin" )
def update( request, server, data ):
    srv = get_object_or_404( Mumble, id=int(server) )
    for record in data:
        if record['id'] == -1:
            if record['delete']:
                continue
            mu = MumbleUser( server=srv )
        else:
            mu = MumbleUser.objects.get( id=record['id'] )
            if record['delete']:
                mu.delete()
                continue

        mu.name     = record['name']
        mu.password = record['password']
        if record['owner']:
            mu.owner = User.objects.get( id=int(record['owner']) )
        mu.save()
        mu.aclAdmin = record['admin']
    return { 'success': True }

@login_required
@csrf_exempt
def update_avatar( request, userid ):
    try:
        user = MumbleUser.objects.get( id=userid )
    except MumbleUser.DoesNotExist:
        return HttpResponse( "false", content_type="text/html" )

    textureform = MumbleTextureForm( request.POST, request.FILES )
    if textureform.is_valid():
        if textureform.cleaned_data['usegravatar'] and user.gravatar:
            user.setTextureFromUrl( user.gravatar )
        else:
            user.setTexture( Image.open( textureform.cleaned_data['texturefile'] ) )
        return HttpResponse( "true", content_type="text/html" )

    return HttpResponse( "false", content_type="text/html" )

def mmng_tree( request, server ):
    """ Return a JSON representation of the channel tree suitable for
        Murmur Manager:
          http://github.com/cheald/murmur-manager/tree/master/widget/

        To make the client widget query this view, set the URL attribute
        to "http://<mumble-django base URL>/mumble"
    """

    srv = get_object_or_404( Mumble, id=int(server) )

    chanlist = []
    userlist = []

    for chanid in srv.channels:
        channel = srv.channels[chanid]

        if channel.parent is not None:
            parent = channel.parent.chanid
        else:
            parent = -1

        chanlist.append({
            "type":     "channel",
            "id":       channel.chanid,
            "name":     channel.name,
            "parent":   parent,
            "position": channel.position,
            "state":    channel.temporary and "temporary" or "permanent"
            })

    for sessionid in srv.players:
        user = srv.players[sessionid]
        userlist.append({
            "type":    "player",
            "name":    user.name,
            "channel": user.channel.chanid,
            "mute":    user.mute or user.selfMute or user.suppress,
            "deaf":    user.deaf or user.selfDeaf,
            "online":  user.onlinesecs,
            "state":   "online"
            })

    if "callback" in request.GET:
        prefix = request.GET["callback"]
        validate_jsonp_callback(prefix)
    else:
        prefix = ""

    return HttpResponse(
        prefix + "(" + json.dumps( { 'channels': chanlist, 'users': userlist } ) + ")",
        content_type='text/javascript'
        )


def cvp_checkauth( request, srv ):
    """ Check if the user is allowed to see private fields. """
    # http://www.djangosnippets.org/snippets/243/
    if srv.isUserAdmin( request.user ):
        return True
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # NOTE: We only support basic authentication for now.
            if auth[0].lower() == "basic":
                import base64
                from django.contrib.auth import authenticate
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active and srv.isUserAdmin( user ):
                    return True
    return False

def cvp_json( request, server ):
    """ JSON reference implementation for the Channel Viewer Protocol.

        See <http://mumble.sourceforge.net/Channel_Viewer_Protocol>
    """
    srv = get_object_or_404( Mumble, id=int(server) )
    ret = json.dumps( srv.asDict( cvp_checkauth( request, srv ) ) )

    if "callback" in request.GET:
        validate_jsonp_callback(request.GET["callback"])
        ret = "%s(%s)" % ( request.GET["callback"], ret )

    return HttpResponse( ret, content_type='application/json' )

def cvp_xml( request, server ):
    """ XML reference implementation for the Channel Viewer Protocol.

        See <http://mumble.sourceforge.net/Channel_Viewer_Protocol>
    """
    from xml.etree.cElementTree import tostring as xml_to_string
    srv = get_object_or_404( Mumble, id=int(server) )
    return HttpResponse(
        '<?xml version="1.0" encoding="UTF-8" ?>'+\
        xml_to_string( srv.asXml( cvp_checkauth( request, srv ) ), encoding='utf-8' ),
        content_type='text/xml'
        )


def mumbleviewer_tree_xml( request, server ):
    """ Get the XML tree from the server and serialize it to the client. """
    from xml.etree.cElementTree import tostring as xml_to_string
    srv = get_object_or_404( Mumble, id=int(server) )
    return HttpResponse(
        xml_to_string( srv.asMvXml(), encoding='utf-8' ),
        content_type='text/xml'
        )

def mumbleviewer_tree_json( request, server ):
    """ Get the Dict from the server and serialize it as JSON to the client. """
    srv = get_object_or_404( Mumble, id=int(server) )

    if "jsonp_callback" in request.GET:
        prefix = request.GET["jsonp_callback"]
        validate_jsonp_callback(prefix)
    else:
        prefix = ""

    return HttpResponse(
        prefix + "(" + json.dumps( srv.asMvJson() ) + ")",
        content_type='text/javascript'
        )
