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


class AdminAuthedTestCase( TestCase ):
    fixtures = ["testdb.json"]

    def setUp( self ):
        TestCase.setUp( self )
        if not self.cl.login( username="svedrin", password="passwort" ):
            raise Exception( "Login failed" )

class UserAuthedTestCase( TestCase ):
    fixtures = ["testdb.json"]

    def setUp( self ):
        TestCase.setUp( self )
        if not self.cl.login( username="nocheinuser", password="passwort" ):
            raise Exception( "Login failed" )


class UnauthedMumbleFormTestCase( ExtDirectFormTestMixin, TestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleForm"

    def testFormGet( self ):
        result = self.formGet( [{'pk': 1}] )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPost( self ):
        result = self.formPost( {'pk': 1, 'url': '', 'player': ''} )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )


class AuthedMumbleFormTestCase( ExtDirectFormTestMixin, AdminAuthedTestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleForm"

    def testFormGet( self ):
        result = self.formGet( [{'pk': 1}] )
        self.assertEquals( result['success'], True, ("errors" in result and result['errors'] or None) )

    def testFormPostSrvAdmin( self ):
        result = self.formPost( {'pk': 1, 'name': 'test server', 'url': '', 'player': ''} )
        self.assertEquals( result['success'], True, ("errors" in result and result['errors'] or None) )

    def testFormPostNonSrvAdmin( self ):
        result = self.formPost( {'pk': 2, 'name': 'alealejandro', 'url': '', 'player': ''} )
        self.assertEquals( result['success'], True, ("errors" in result and result['errors'] or None) )


class UnauthedMumbleUserFormTestCase( ExtDirectFormTestMixin, TestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleUserForm"

    def testFormGet( self ):
        result = self.formGet( [{'pk': 1}] )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPostWithoutServer( self ):
        result = self.formPost( {'pk': 1, 'name': "ohai", 'password': "failfail"} )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPost( self ):
        result = self.formPost( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1} )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

class AuthedMumbleUserFormTestCase( ExtDirectFormTestMixin, AdminAuthedTestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleUserForm"

    def testFormGet( self ):
        result = self.formGet( [{'pk': 1}] )
        self.assertEquals( result['success'], True, ("errors" in result and result['errors'] or None) )

    def testFormPostWithoutServer( self ):
        result = self.formPost( {'pk': 1, 'name': "svedrin", 'password': 'passwort' } )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'pre-validation failed' )

    def testFormPost( self ):
        result = self.formPost( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1} )
        self.assertEquals( result['success'], True, ("errors" in result and result['errors'] or None) )

class UnauthedMumbleUserLinkFormTestCase( UnauthedMumbleUserFormTestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleUserLinkForm"

    def testFormGet( self ):
        result = self.formGet( [{'pk': 1}] )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPost( self ):
        result = self.formPost( {'pk': 1, 'name': "ohai", 'password': 'failfail', 'serverid': 1} )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

class AuthedMumbleUserLinkFormTestCase( ExtDirectFormTestMixin, AdminAuthedTestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleUserLinkForm"

    def testFormGet( self ):
        if settings.ALLOW_ACCOUNT_LINKING:
            # Excepts because linkacc can't be retrieved, but this form is for being
            # displayed when empty only so retrieval is either forbidden or an error
            self.assertRaises( Exception, self.formGet, [{'pk': 1}] )
        else:
            result = self.formGet( [{'pk': 1}] )
            self.assertEquals( result['success'], False )
            self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPost( self ):
        result = self.formPost( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1} )
        if settings.ALLOW_ACCOUNT_LINKING:
            self.assertEquals( result['success'], True, ("errors" in result and result['errors'] or None) )
        else:
            self.assertEquals( result['success'], False )
            self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPostLinking( self ):
        result = self.formPost( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1, 'linkacc': 'on'} )
        self.assertEquals( result['success'], False )

class UserMumbleUserLinkFormTestCase( ExtDirectFormTestMixin, UserAuthedTestCase ):
    api_baseurl = "/mumble/forms"
    formname = "MumbleUserLinkForm"
    def testFormGet( self ):
        # Request someone who isn't me
        result = self.formGet( [{'pk': 1}] )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPostEdit( self ):
        # Edit someone who isn't me
        result = self.formPost( {'pk': 1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1} )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors'][''], 'access denied' )

    def testFormPostEdit( self ):
        # Try registering taken account
        result = self.formPost( {'pk': -1, 'name': "svedrin", 'password': 'passwort', 'serverid': 1} )
        self.assertEquals( result['success'], False )
        self.assertEquals( result['errors']['name'], 'Another player already registered that name.' )

    def testFormPostLinkingUser( self ):
        result = self.formPost( {'pk': -1, 'name': "nichtadmin", 'password': 'nichtadmin', 'serverid': 1, 'linkacc': 'on'} )
        self.assertEquals( result['success'], settings.ALLOW_ACCOUNT_LINKING )

    def testFormPostLinkingAdmin( self ):
        result = self.formPost( {'pk': -1, 'name': "dochadmin", 'password': 'dochadmin', 'serverid': 1, 'linkacc': 'on'} )
        self.assertEquals( result['success'], (settings.ALLOW_ACCOUNT_LINKING and settings.ALLOW_ACCOUNT_LINKING_ADMINS) )


class UnauthedFormLoading(TestCase):
    """ Makes unauthorized requests to forms which require auth, and checks
        that those handle auth correctly.
    """
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

