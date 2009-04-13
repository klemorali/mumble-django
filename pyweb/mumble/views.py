# -*- coding: utf-8 -*-
""" This file is part of the mumble-django application.
    
    Copyright (C) 2009, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 
    All rights reserved.
 
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
 
    - Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    - Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    - Neither the name of the Mumble Developers nor the names of its
      contributors may be used to endorse or promote products derived from this
      software without specific prior written permission.
 
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
    A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from django.shortcuts			import render_to_response, get_object_or_404, get_list_or_404
from django.template			import RequestContext
from django.http			import HttpResponseRedirect
from django.core.urlresolvers		import reverse
from django.contrib.auth.decorators	import login_required

from models				import Mumble, MumbleUser
from forms				import *
from mmobjects				import mmServer, mmChannel

# Handler class for all Server specific views

class Storage( object ):
	s = list();
	r = None;

def mumbles( request ):
	"Displays a list of all configured Mumble servers."
	return render_to_response(
		'mumble/list.htm',
		{ 'MumbleObjects': get_list_or_404( Mumble ) },
		context_instance = RequestContext(request)
		);

def show( request, server ):
	"Displays the channel list for the given Server ID."
	srv, o = createChannelList( server );
	
	isAdmin = srv.isUserAdmin( request.user );
	
	if isAdmin:
		if request.method == 'POST' and "mode" in request.POST and request.POST['mode'] == 'admin':
			adminform = MumbleForm( request.POST, instance=srv );
			if adminform.is_valid():
				adminform.save();
				return HttpResponseRedirect( '/mumble/%d' % int(server) );
		else:
			adminform = MumbleForm( instance=srv );
	else:
		adminform = None;
	
	registered = False;
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
	else:
		regform = None;
	
	return render_to_response(
		'mumble/mumble.htm',
		{
			'DBaseObject':  srv,
			'ServerObject': o,
			'ChannelTable': Storage.s,
			"CurrentUserIsAdmin": isAdmin,
			"AdminForm":    adminform,
			"RegForm":      regform,
			"Registered":   registered,
		},
		context_instance = RequestContext(request)
		);

def showContent( server, user = None ):
	"Renders and returns the channel list for the given Server ID."
	from django.template import Context, loader
	
	srv, o = createChannelList( server );
	
	mumbleAcc = None;
	if user.is_authenticated():
		mmUsers = MumbleUser.objects.filter( owner = user );
		if mmUsers:
			mumbleAcc = mmUsers[0];
	
	t_content = loader.get_template( 'mumble/content.htm' );
	c_content = Context( {
		'DBaseObject': srv,
		'ServerObject': o,
		'ChannelTable': Storage.s,
		'user': user,
		'mumbleAccount': mumbleAcc,
		"CurrentUserIsAdmin": srv.isUserAdmin( request.user ),
		} );
	r_content = t_content.render( c_content );
	
	return r_content;


def createChannelList( server ):
	"Renders the channel list."
	srv = get_object_or_404( Mumble, id=server );
	
	o = srv.getServerObject();
	
	Storage.s = list();
	Storage.r = o.channels[0];
	o.channels[0].visit( renderListItem, 0 );
	
	return srv, o;


def renderListItem( item, level ):
	"Stores a line in the channel list."
	if item == Storage.r:
		return;
	
	# Filter channels that don't have players in them and are not a subchannel of root
	if level > 1 and item.playerCount == 0:
		# I used to test if item is an instance of mmChannel here. For some reason, that doesn't work. Dunno why.
		return;
	
	if isinstance( item, mmChannel ):
		Storage.s.append( ( level, item, item.parentChannels() ) );
	else:
		Storage.s.append( ( level, item ) );



@login_required
def register( request, server ):
	# Register the current user with this mumble server, or give them a form to change their registration data.
	srv = Mumble.objects.get( id=server );
	
	if request.user.is_authenticated():
		try:
			reg = MumbleUser.objects.get( server=srv, owner=request.user );
		except MumbleUser.DoesNotExist:
			reg = None;
	else:
		reg = None;
	
	return render_to_response(
		'mumble/reg.htm',
		{ 'Mumble': srv, 'Reg': reg },
		context_instance = RequestContext(request)
		);

@login_required
def savereg( request ):
	srv  = Mumble.objects.get( id=request.POST['server'] );
	
	if request.method == 'POST':
		try:
			user  = MumbleUser.objects.get( server=srv, owner=request.user );
		except MumbleUser.DoesNotExist:
			form  = MumbleUserForm( request.POST );
			if form.is_valid():
				model = form.save( commit=False );
				model.isAdmin = False;
				model.server  = srv;
				model.save();
		else:
			form = MumbleForm( request.POST, instance=user );
			if form.is_valid():
				model.save();
		
		return HttpResponseRedirect( '/mumble/%d' % int(serverid) );
	else:
		form = MumbleForm( instance=murmur );
	
	return render_to_response(
		'mumble/admin.htm',
		{ "Mumble": murmur, "Adminform": form, "CurrentUserIsAdmin": murmur.isUserAdmin( request.user ) },
		context_instance = RequestContext(request)
		);



@login_required
def admin( request, serverid ):
	murmur = get_object_or_404( Mumble, id=serverid );
	
	if request.method == 'POST':
		form = MumbleForm( request.POST, instance=murmur );
		if form.is_valid():
			form.save();
			return HttpResponseRedirect( '/mumble/%d' % int(serverid) );
	else:
		form = MumbleForm( instance=murmur );
	
	return render_to_response(
		'mumble/admin.htm',
		{ "Mumble": murmur, "Adminform": form, "CurrentUserIsAdmin": murmur.isUserAdmin( request.user ) },
		context_instance = RequestContext(request)
		);





