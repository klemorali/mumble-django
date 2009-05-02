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

from django.shortcuts			import render_to_response, get_object_or_404, get_list_or_404
from django.template			import RequestContext
from django.http			import HttpResponseRedirect
from django.core.urlresolvers		import reverse
from django.contrib.auth.decorators	import login_required
from django.contrib.auth.models		import User

from mumble.models			import Mumble, MumbleUser
#from guestbook.models			import Entry, Comment
#from forum.models			import Post

@login_required
def profile( request ):
	userdata = {
		"ProfileActive": True,
		"mumbleaccs":	MumbleUser.objects.filter(	owner  = request.user ),
#		"gbposts": 	Entry.objects.filter(		author = request.user ).count(),
#		"gbcomments": 	Comment.objects.filter(		author = request.user ).count(),
#		"forumposts": 	Post.objects.filter(		author = request.user ).count(),
		};
	
	return render_to_response(
		'registration/profile.html',
		userdata,
		context_instance = RequestContext(request)
		);


def imprint( request ):
	return render_to_response( 'registration/imprint.html', {}, context_instance = RequestContext(request) );
