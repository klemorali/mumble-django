# -*- coding: utf-8 -*-
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
	return render_to_response( 'registration/imprint.html' );
