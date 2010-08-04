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

from django.conf.urls.defaults import url, patterns, include
from django.conf import settings

from views import EXT_DIRECT_PROVIDER
from forms import EXT_FORMS_PROVIDER

urlpatterns = patterns(
    'mumble.views',
    ( r'djangousers',               'djangousers' ),
    ( r'(?P<server>\d+)/users',     'users'       ),

    ( r'api/',                      include(EXT_DIRECT_PROVIDER.urls) ),
    ( r'forms/',                    include(EXT_FORMS_PROVIDER.urls)  ),

    ( r'(?P<server>\d+)/(?P<userid>\d+)/texture.png',    'showTexture' ),
    ( r'(?P<userid>\d+)/update_avatar',      'update_avatar'  ),

    ( r'murmur/tree/(?P<server>\d+)',        'mmng_tree'             ),
    ( r'mumbleviewer/(?P<server>\d+).xml',   'mumbleviewer_tree_xml' ),
    ( r'mumbleviewer/(?P<server>\d+).json',  'mumbleviewer_tree_json'),

    ( r'mobile/(?P<server>\d+)$',            'mobile_show'     ),
    ( r'mobile/?$',                          'mobile_mumbles'  ),

    ( r'(?P<server>\d+).json',               'cvp_json'        ),
    ( r'(?P<server>\d+).xml',                'cvp_xml'         ),

    ( r'(?P<server>\d+)$',                   'show'            ),
    ( r'$',                                  'mumbles'         ),
)

if settings.DEBUG or True:
    # The following is a fake, to not break old installations. You should
    # really serve this stuff through the web server directly.
    from os.path import join, dirname, abspath, exists
    mediadir = join( dirname(abspath(__file__)), 'media' )
    print mediadir
    urlpatterns.insert( 1, url(r'^media/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': mediadir, 'show_indexes': True} ),
    )
