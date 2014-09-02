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

from django.conf.urls import patterns, include
from django.contrib import admin

from django.conf import settings

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'

js_info_dict = {
    'packages': ('mumble',),
}

urlpatterns = patterns('',
    (r'^/?$',               'mumble.views.redir' ),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^accounts/profile/', 'views.profile' ),
    (r'^accounts/imprint/', 'views.imprint' ),

    (r'^mumble/',           include('mumble.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/',            admin.site.urls),

    (r'^i18n/',             include('django.conf.urls.i18n')),
     (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
)

if "registration" in settings.INSTALLED_APPS:
    urlpatterns += patterns( '',
        (r'^accounts/',         include('registration.backends.default.urls') ),
    )

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += patterns( '',
        ( r'rosetta/', include( 'rosetta.urls' ) )
    )

# Development stuff
if settings.DEBUG or True:
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
        'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True} ),
    )

