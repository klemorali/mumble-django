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

from models				import Mumble, MumbleUser
from forms				import *
from mmobjects				import *



def mumbles( request ):
	"Displays a list of all configured Mumble servers, or redirects if only one configured."
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
	"Displays the channel list for the given Server ID."
	srv = get_object_or_404( Mumble, id=server );
	
	isAdmin = srv.isUserAdmin( request.user );
	
	# The tab to start on.
	displayTab = 0;
	
	if isAdmin:
		if request.method == 'POST' and "mode" in request.POST and request.POST['mode'] == 'admin':
			adminform = MumbleForm( request.POST, instance=srv );
			# In case we redisplay the page, it was displayed with errors on the admin form, so tell
			# Ext to show the admin form tab first.
			displayTab = 1;
			if adminform.is_valid():
				adminform.save();
				return HttpResponseRedirect( '/mumble/%d' % int(server) );
		else:
			adminform = MumbleForm( instance=srv );
	else:
		adminform = None;
	
	registered = False;
	user = None;
	
	if request.user.is_authenticated():
		if request.method == 'POST' and 'mode' in request.POST and request.POST['mode'] == 'reg':
			try:
				user    = MumbleUser.objects.get( server=srv, owner=request.user );
			except MumbleUser.DoesNotExist:
				regform = MumbleUserForm( request.POST );
				if regform.is_valid():
					model = regform.save( commit=False );
					model.isAdmin = False;
					model.server  = srv;
					model.owner   = request.user;
					model.save();
					return HttpResponseRedirect( '/mumble/%d' % int(server) );
			else:
				regform = MumbleUserForm( request.POST, instance=user );
				if regform.is_valid():
					regform.save();
					return HttpResponseRedirect( '/mumble/%d' % int(server) );
		else:
			try:
				user  = MumbleUser.objects.get( server=srv, owner=request.user );
			except MumbleUser.DoesNotExist:
				regform = MumbleUserForm();
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
		if id != 0:
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


def showTexture( request, server ):
	if request.user.is_authenticated():
		srv  = Mumble.objects.get( id=int(server) );
		user = MumbleUser.objects.get( server=srv, owner=request.user );
		try:
			img  = user.getTexture();
		except ValueError:
			raise Http404();
		else:
			buffer = StringIO();
			img.save( buffer, "PNG" );
			return HttpResponse( buffer.getvalue(), "image/png" );
	raise Http404();



