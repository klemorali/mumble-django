# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *
 *  djExtDirect is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

def login( request, username, passwd ):
    from django.contrib.auth import authenticate, login as djlogin
    if request.user.is_authenticated():
        return { 'success': True }
    user = authenticate( username=username, password=passwd )
    if user:
        if user.is_active:
            djlogin( request, user )
            return { 'success': True }
        else:
            return { 'success': False, 'error': 'account disabled' }
    else:
        return { 'success': False, 'error': 'invalid credentials' }

def logout( request ):
    from django.contrib.auth import logout as djlogout
    djlogout( request )
    return { 'success': True }
