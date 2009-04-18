# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns(
	'',
	( r'(?P<server>\d+)',		'mumble.views.show' ),
	( r'$',				'mumble.views.mumbles' ),
)
