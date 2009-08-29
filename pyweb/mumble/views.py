# -*- coding: utf-8 -*-

"""
 *  Copyright (C) 2009, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

from StringIO				import StringIO

from django.shortcuts			import render_to_response, get_object_or_404, get_list_or_404
from django.template			import RequestContext
from django.http			import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers		import reverse
from django.contrib.auth.decorators	import login_required
from django.conf			import settings

from models				import Mumble, MumbleUser
from forms				import *
from mmobjects				import *



def mumbles( request ):
	"""Display a list of all configured Mumble servers, or redirects if only one configured."""
	mumbles = get_list_or_404( Mumble );
	
	if len(mumbles) == 1:
		return HttpResponseRedirect( '/mumble/%d' % mumbles[0].id );
	
	return render_to_response(
		'mumble/list.htm',
		{ 'MumbleObjects': mumbles,
		  'MumbleActive':  True,
		},
		context_instance = RequestContext(request)
		);


def show( request, server ):
	"""Display the channel list for the given Server ID.
	
	This includes not only the channel list itself, but indeed the user registration,
	server admin and user texture form as well. The template then uses JavaScript
	to display these forms integrated into the Channel viewer.
	"""
	srv = get_object_or_404( Mumble, id=server );
	
	isAdmin = srv.isUserAdmin( request.user );
	
	# The tab to start on.
	displayTab = 0;
	
	if isAdmin:
		if request.method == 'POST' and "mode" in request.POST and request.POST['mode'] == 'admin':
			adminform = MumbleForm( request.POST, instance=srv );
			if adminform.is_valid():
				adminform.save();
				return HttpResponseRedirect( '/mumble/%d' % int(server) );
			else:
				displayTab = 2;
		else:
			adminform = MumbleForm( instance=srv );
	else:
		adminform = None;
	
	registered = False;
	user = None;
	
	if request.user.is_authenticated():
		# Unregistered users may or may not need a password to register.
		if settings.PROTECTED_MODE and srv.passwd:
			unregged_user_form = MumbleUserPasswordForm;
		else:
			unregged_user_form = MumbleUserForm;
		
		if request.method == 'POST' and 'mode' in request.POST and request.POST['mode'] == 'reg':
			try:
				user    = MumbleUser.objects.get( server=srv, owner=request.user );
			except MumbleUser.DoesNotExist:
				regform = unregged_user_form( request.POST );
				regform.server = srv;
				if regform.is_valid():
					model = regform.save( commit=False );
					model.isAdmin = False;
					model.server  = srv;
					model.owner   = request.user;
					model.save();
					return HttpResponseRedirect( '/mumble/%d' % int(server) );
				else:
					displayTab = 1;
			else:
				regform = MumbleUserForm( request.POST, instance=user );
				if regform.is_valid():
					regform.save();
					return HttpResponseRedirect( '/mumble/%d' % int(server) );
				else:
					displayTab = 1;
		else:
			try:
				user  = MumbleUser.objects.get( server=srv, owner=request.user );
			except MumbleUser.DoesNotExist:
				regform = unregged_user_form();
			else:
				regform = MumbleUserForm( instance=user );
				registered = True;
		
		if request.method == 'POST' and 'mode' in request.POST and request.POST['mode'] == 'texture' and registered:
			textureform = MumbleTextureForm( request.POST, request.FILES );
			if textureform.is_valid():
				user.setTexture( request.FILES['texturefile'] );
				return HttpResponseRedirect( '/mumble/%d' % int(server) );
		else:
			textureform = MumbleTextureForm();
	
	else:
		regform = None;
		textureform = None;
	
	# ChannelTable is a somewhat misleading name, as it actually contains channels and players.
	channelTable = [];
	for id in srv.channels:
		if id != 0 and srv.channels[id].show:
			channelTable.append( srv.channels[id] );
	for id in srv.players:
		channelTable.append( srv.players[id] );
	
	
	return render_to_response(
		'mumble/mumble.htm',
		{
			'DBaseObject':  srv,
			'ChannelTable': channelTable,
			'CurrentUserIsAdmin': isAdmin,
			'AdminForm':    adminform,
			'RegForm':      regform,
			'TextureForm':  textureform,
			'Registered':   registered,
			'DisplayTab':   displayTab,
			'MumbleActive': True,
			'MumbleAccount':user,
		},
		context_instance = RequestContext(request)
		);


def showTexture( request, server, userid = None ):
	"""Pack the currently logged in user's texture (if any) into an HttpResponse."""
	srv  = get_object_or_404( Mumble, id=int(server) );
	
	if userid is None:
		if request.user.is_authenticated():
			user = get_object_or_404( MumbleUser, server=srv, owner=request.user );
		else:
			raise Http404();
	else:
		user = get_object_or_404( MumbleUser, server=srv, id=int(userid) );
	
	try:
		img  = user.getTexture();
	except ValueError:
		raise Http404();
	else:
		buffer = StringIO();
		img.save( buffer, "PNG" );
		return HttpResponse( buffer.getvalue(), "image/png" );



