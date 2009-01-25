from models import *
from django.contrib import admin

class MumbleAdmin(admin.ModelAdmin):
	list_display   = [ 'name', 'addr', 'port', 'booted' ];
	list_filter    = [ 'booted' ];
	search_fields  = [ 'name', 'addr' ];
	ordering       = [ 'name' ];

class MumbleUserAdmin(admin.ModelAdmin):
	list_display   = [ 'owner', 'server', 'name' ];
	list_filter    = [ 'server' ];
	search_fields  = [ 'owner__username', 'name' ];
	ordering       = [ 'owner__username' ];


admin.site.register( Mumble, MumbleAdmin );
admin.site.register( MumbleUser, MumbleUserAdmin );
