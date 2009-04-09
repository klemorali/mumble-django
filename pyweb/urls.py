from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    # Example:
    # (r'^mumble_django/', include('mumble_django.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^accounts/profile/', 'views.profile' ),
    (r'^accounts/',         include('registration.urls')),

    (r'^mumble/',           include('mumble.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)

# Development stuff
if settings.DEBUG:
        urlpatterns += patterns('',
                (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True} ),
		(r'^/?$',                  'django.views.generic.simple.redirect_to', { 'url': '/mumble/' } ),
        )

