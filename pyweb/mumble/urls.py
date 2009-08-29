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

from django.conf.urls.defaults import *

urlpatterns = patterns(
	'mumble.views',
	( r'(?P<server>\d+)/users',				'users'	),
	( r'(?P<server>\d+)/(?P<userid>\d+)texture.png',	'showTexture'	),
	( r'(?P<server>\d+)/texture.png',			'showTexture'	),
	( r'(?P<server>\d+)',					'show'		),
	( r'$',							'mumbles'	),
)
