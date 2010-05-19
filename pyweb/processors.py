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

def installed_apps(request):
    from django.conf import settings
    return { 'ROSETTA_INSTALLED': "rosetta" in settings.INSTALLED_APPS }

def mumble_version(request):
    from mumble import version_str
    return { 'CURRENTVERSION': version_str }

def theme_url(request):
    from django.conf import settings
    if settings.THEME:
        return { 'THEME_URL': settings.THEME_URL }
    else:
        return {}
