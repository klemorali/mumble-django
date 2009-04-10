from django.conf.urls.defaults import *

urlpatterns = patterns(
	'',
	( r'savereg',			'mumble.views.savereg' ),
	( r'reg/(?P<server>\d+)',	'mumble.views.register' ),
	( r'admin/(?P<serverid>\d+)',	'mumble.views.admin' ),
	( r'(?P<server>\d+)',		'mumble.views.show' ),
	( r'$',				'mumble.views.mumbles' ),
)
