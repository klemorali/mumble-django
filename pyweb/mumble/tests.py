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

# Privs:
#
# Unauthed users:
# * Registration:    no                                 Anon_MumbleUser{,Link}FormTestCase
# * Administration:  no                                 Anon_MumbleFormTestCase
# * User texture:    no
# * User list:       no
# * Log messages:    no
# * Instance scope:  ALL
#
# Authed users, unregistered:
# * Registration:    self, User{,Password,Link}Form     User_MumbleUserLinkFormTestCase
# * Administration:  no
# * User texture:    no
# * User list:       no
# * Log messages:    no
# * Instance scope:  CURRENT
#
# Authed users, not admins:
# * Registration:    self, UserForm
# * Administration:  no
# * User texture:    self
# * User list:       no
# * Log messages:    no
# * Instance scope:  CURRENT
#
# Authed users, admins:
# * Registration:    everyone
# * Administration:  yes
# * User texture:    everyone
# * User list:       yes
# * Log messages:    yes
# * Instance scope:  CURRENT
#
# Authed users, superadmins:
# * Registration:    everyone                           Super_MumbleUser{,Link}FormTestCase
# * Administration:  yes                                Super_MumbleFormTestCase
# * User texture:    everyone
# * User list:       yes
# * Log messages:    yes
# * Instance scope:  ALL

import simplejson
from django.conf        import settings
from django.test        import TestCase
from django.test.client import Client
from django.contrib.auth.models import User

from models             import Mumble, MumbleUser
from utils              import ObjectInfo

class ExtDirectFormTestMixin(object):
    """ Methods for testing a Form exported via Ext.Direct.
        These only define the methods, you will need to inherit your TestCase
        from this class and set the following class attributes:

        api_baseurl:
          The URL under which the Ext.Direct provider has been registered.
        formname:
          The name of the exported form class.
    """
    def setUp(self):
        self.cl = Client()
        super(ExtDirectFormTestMixin, self).setUp()
        self.tid = 1

    def testFormApi(self):
        rawr = self.cl.get( "%s/%s.js" % ( self.api_baseurl, self.formname.lower() ) )
        self.assertEquals( rawr.status_code, 200 )

    def formGet( self, data=[] ):
        rawr = self.cl.post( self.api_baseurl+'/router',
            data=simplejson.dumps({
                'tid':    self.tid,
                'action': ('XD_%s' % self.formname),
                'method': 'get',
                'data':   data,
                'type':   'rpc'
                }),
            content_type='application/json' )
        self.tid += 1
        response = simplejson.loads(rawr.content)
        if response['type'] == "exception":
            raise Exception( response["message"] )
        self.assert_( "result" in response )
        return response['result']

    def formPost( self, data={} ):
        postdata={
            'extAction': ('XD_%s' % self.formname),
            'extMethod': 'update',
            'extTID':    self.tid,
            'extType':   'rpc',
            'extUpload': 'false',
            }
        self.tid += 1
        postdata.update( data )
        rawr = self.cl.post( self.api_baseurl+'/router', data=postdata )
        response = simplejson.loads(rawr.content)
        if response['type'] == "exception":
            raise Exception( response["message"] )
        self.assert_( "result" in response )
        return response['result']


def generateTestCase( name, formname, data, login=None ):
    attrs = {
        'fixtures':    ['testdb.json'],
        'formname':    formname,
        'api_baseurl': '/mumble/forms',
        }

    if login:
        def setUp( self ):
            ExtDirectFormTestMixin.setUp( self )
            if not self.cl.login( **login ):
                raise Exception( "Login failed" )
        attrs['setUp'] = setUp

    def mkGet( data, result ):
        def testFormGet( self ):
            callresult = self.formGet( [{ 'pk': data['pk'] }] )
            if "data" in callresult:
                del callresult['data'] # don't care
            self.assertEquals( callresult, result )
        return testFormGet

    def mkPost( data, result ):
        def testFormPost( self ):
            callresult = self.formPost( data )
            self.assertEquals( callresult, result,
                ("errors" in callresult and callresult['errors'] or None)
                )
        return testFormPost

    for testname in data:
        if len(data[testname]) == 3:
            testdata, getresult, postresult = data[testname]
        else:
            testdata, getresult = data[testname]
            postresult = getresult

        attrs.update({
            ('testForm%sGet'  % testname):  mkGet( testdata,  getresult ),
            ('testForm%sPost' % testname): mkPost( testdata, postresult ),
            })

    return type( name, (ExtDirectFormTestMixin, TestCase), attrs )

RES_SUCCESS      = {'success': True}
RES_ACCESSDENIED = {'success': False, 'errors': {'': 'access denied'}}
RES_PREVALFAIL   = {'success': False, 'errors': {'': 'pre-validation failed'}}

LOGIN_SUPERADMIN = {'username': 'svedrin', 'password': 'passwort'}
LOGIN_UNREGUSER  = {'username': 'unreg',   'password': 'passwort'}
LOGIN_USER       = {'username': 'user',    'password': 'passwort'}
LOGIN_ADMIN      = {'username': 'admin',   'password': 'passwort'}

#############################################################
###      ANON: Unauthed (not logged in) users             ###
#############################################################

Anon_Registration = generateTestCase(
    name = "Anon_Registration",
    formname = "MumbleUserForm",
    data = {
        'My':    ( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1}, RES_ACCESSDENIED ),
        'Other': ( {'pk': 1, 'name': "svedrin", 'password': 'passwort'}, RES_ACCESSDENIED )
        }
    )

Anon_Administration = generateTestCase(
    name     = "Anon_Administration",
    formname = "MumbleForm",
    data     = { 'My': ( {'pk': 1, 'url': '', 'player': ''}, RES_ACCESSDENIED ) },
    )

Anon_UserLink = generateTestCase(
    name = "Anon_UserLink",
    formname = "MumbleUserLinkForm",
    data = {
        'My':    ( {'pk': 1, 'name': "ohai", 'password': 'failfail', 'serverid': 1}, RES_ACCESSDENIED ),
        }
    )

#############################################################
###      UNREG: Authenticated but no MumbleUser avail     ###
#############################################################

Unreg_Registration = generateTestCase(
    name = "Unreg_Registration",
    formname = "MumbleUserForm",
    data = {
        'My':    ( {'pk': -1, 'name': "neueruser", 'password': 'passwort', 'serverid': 1}, RES_SUCCESS ),
        'Taken': ( {'pk': -1, 'name': "svedrin",   'password': 'passwort', 'serverid': 1}, RES_SUCCESS,
                   {'success': False, 'errors': {'name': 'Another player already registered that name.'}} ),
        'Other': ( {'pk':  1, 'name': "svedrin",   'password': 'passwort'}, RES_ACCESSDENIED )
        },
    login = LOGIN_UNREGUSER
    )

if settings.ALLOW_ACCOUNT_LINKING and settings.ALLOW_ACCOUNT_LINKING_ADMINS:
    unreg_adminlinkresult = RES_SUCCESS
else:
    unreg_adminlinkresult = {'success': False, 'errors': {'__all__': 'Linking Admin accounts is not allowed.'}}

Unreg_UserLink = generateTestCase(
    name = "User_UserLink",
    formname = "MumbleUserLinkForm",
    data = {
        'My':    ( {'pk': -1, 'name': "nichtadmin", 'password': 'nichtadmin', 'serverid': 1, 'linkacc': 'on'},
                   RES_ACCESSDENIED, RES_SUCCESS if settings.ALLOW_ACCOUNT_LINKING else RES_ACCESSDENIED ),
        'Admin': ( {'pk': -1, 'name': "dochadmin", 'password': 'dochadmin', 'serverid': 1, 'linkacc': 'on'},
                   RES_ACCESSDENIED, unreg_adminlinkresult ),
        'Other': ( {'pk':  1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1}, RES_ACCESSDENIED ),
        'Taken': ( {'pk': -1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1}, RES_ACCESSDENIED,
                   {'success': False, 'errors':{'name': 'Another player already registered that name.'}} ),
        },
    login = LOGIN_UNREGUSER
    )

Unreg_Administration = generateTestCase(
    name     = "Unreg_Administration",
    formname = "MumbleForm",
    data     = {
        'My':    ( {'pk': 1, 'name': 'test server',  'url': '', 'player': ''}, RES_ACCESSDENIED ),
        'Other': ( {'pk': 2, 'name': 'alealejandro', 'url': '', 'player': ''}, RES_ACCESSDENIED ),
        },
    login    = LOGIN_UNREGUSER,
    )

#############################################################
###      USER: MumbleUser but not a server admin          ###
#############################################################

User_Administration = generateTestCase(
    name     = "User_Administration",
    formname = "MumbleForm",
    data     = {
        'My':    ( {'pk': 1, 'name': 'test server',  'url': '', 'player': ''}, RES_ACCESSDENIED ),
        'Other': ( {'pk': 2, 'name': 'alealejandro', 'url': '', 'player': ''}, RES_ACCESSDENIED ),
        },
    login    = LOGIN_USER,
    )

#############################################################
###      ADMIN: MumbleUser is a server admin              ###
#############################################################

Admin_Administration = generateTestCase(
    name     = "Admin_Administration",
    formname = "MumbleForm",
    data     = {
        'My':    ( {'pk': 1, 'name': 'test server',  'url': '', 'player': ''}, RES_SUCCESS      ),
        'Other': ( {'pk': 2, 'name': 'alealejandro', 'url': '', 'player': ''}, RES_ACCESSDENIED ),
        },
    login    = LOGIN_ADMIN,
    )

#############################################################
###      SUPER: User is superadmin, MumbleUser irrelevant ###
#############################################################

Super_Registration = generateTestCase(
    name = "Super_Registration",
    formname = "MumbleUserForm",
    data = {
        'My':    ( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1}, RES_SUCCESS ),
        'Fail':  ( {'pk': 1, 'name': "svedrin", 'password': 'passwort'}, RES_SUCCESS, RES_PREVALFAIL ),
        },
    login = LOGIN_SUPERADMIN
    )

Super_Administration = generateTestCase(
    name     = "Super_Administration",
    formname = "MumbleForm",
    data     = {
        'My':    ( {'pk': 1, 'name': 'test server',  'url': '', 'player': ''}, RES_SUCCESS ),
        'Other': ( {'pk': 2, 'name': 'alealejandro', 'url': '', 'player': ''}, RES_SUCCESS ),
        },
    login    = LOGIN_SUPERADMIN,
    )

Super_UserLink = generateTestCase(
    name = "Super_UserLink",
    formname = "MumbleUserLinkForm",
    data = {
        'My':    ( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1},
                   RES_ACCESSDENIED ),
        'Link':  ( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1, 'linkacc': 'on'},
                   RES_ACCESSDENIED )
        },
    )

class ExportedForms(TestCase):
    """ Makes sure needed forms are exported, and admin forms are not. """

    def setUp(self):
        self.cl = Client()

    def testMumbleUserFormApi(self):
        rawr = self.cl.get( '/mumble/forms/mumbleuserform.js' )
        self.assertEquals( rawr.status_code, 200 )

    def testMumbleUserPasswordFormApi(self):
        rawr = self.cl.get( '/mumble/forms/mumbleuserpasswordform.js' )
        self.assertEquals( rawr.status_code, 200 )

    def testMumbleUserLinkFormApi(self):
        rawr = self.cl.get( '/mumble/forms/mumbleuserlinkform.js' )
        self.assertEquals( rawr.status_code, 200 )

    def testMumbleAdminFormApi(self):
        # This form is NOT exported (and shouldn't be) because it's only used in the admin
        rawr = self.cl.get( '/mumble/forms/mumbleadminform.js' )
        self.assertEquals( rawr.status_code, 404 )

    def testMumbleUserAdminFormApi(self):
        # This form is NOT exported (and shouldn't be) because it's only used in the admin
        rawr = self.cl.get( '/mumble/forms/mumbleuseradminform.js' )
        self.assertEquals( rawr.status_code, 404 )

