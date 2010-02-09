# -*- coding: utf-8 -*-
# Django settings for mumble_django project.

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

#################################################################
#################################################################
##                                                             ##
##  The path inside the VirtualHost that M-D lives in:         ##
##                                                             ##
MUMBLE_DJANGO_URL  = '/';                                      ##
#MUMBLE_DJANGO_URL  = '/mumble-django/';                       ##
##                                                             ##
##  Make sure you use a trailing slash!                        ##
##                                                             ##
#################################################################
##                                                             ##
##  Mumble-Django will try to auto-detect this value if it     ##
##  isn't set, which is the default. However, if this should   ##
##  not work as expected, set this to the path where you       ##
##  extracted Mumble-Django.                                   ##
##                                                             ##
##  Default: Auto Detection                                    ##
MUMBLE_DJANGO_ROOT = None;                                     ##
##  Examples:                                                  ##
#MUMBLE_DJANGO_ROOT = '/srv/mumble-django';                    ##
#MUMBLE_DJANGO_ROOT = 'c:/web/mumble-django';                  ##
##                                                             ##
#################################################################
##                                                             ##
##  For a basic installation, this is all you need to edit in  ##
##  this file, the rest will be handled automatically!         ##
##                                                             ##
#################################################################
#################################################################


from os.path import join, dirname, abspath, exists
if not MUMBLE_DJANGO_ROOT or not exists( MUMBLE_DJANGO_ROOT ):
	MUMBLE_DJANGO_ROOT = dirname(dirname(abspath(__file__)));


# The ICE interface version to use. This variable is only used if SLICE is set to None.
#SLICE_VERSION = (1, 1, 8)
SLICE_VERSION = (1, 2, 2)
# Murmur 1.2.0 is incompatible with 1.1.8, that's why this needs to be configured here.
# If you have <=1.1.8 and 1.2.x servers running simultaneously, consider using DBus for
# the <=1.1.8 servers and ICE for 1.2.x. That way, you will be able to manage both server
# versions with the same install of Mumble-Django, without losing any functionality.

# The slice to use for communication over ZeroC ICE.
# This can be set to the path to the Murmur.ice file that resides in your Murmur directory.
# Default: None -- use the slices shipped with MD. If you choose to do this, make sure you
#          set the SLICE_VERSION variable above!
SLICE = None


# The default connection string to set for newly created instances.
# ICE:
DEFAULT_CONN = 'Meta:tcp -h 127.0.0.1 -p 6502'
# DBus:
#DEFAULT_CONN = 'net.sourceforge.mumble.murmur'

# Default email address to send mails from.
DEFAULT_FROM_EMAIL = "webmaster@localhost"

# Length of the account activation period, in days.
ACCOUNT_ACTIVATION_DAYS = 30

# Default mumble port. If your server runs under this port, it will not be included in the links in the Channel Viewer.
MUMBLE_DEFAULT_PORT = 64738

# Should subchannels be shown, even if there are no players in them?
SHOW_EMPTY_SUBCHANS = False

# Protect the registration form for private servers?
# If set to True, people will need to enter the server password in order to create accounts,
# and will not be able to link existing accounts.
PROTECTED_MODE = False

# Account linking allows users who registered their accounts through Mumble instead of using
# Mumble-Django, to tell MD that this account belongs to them. Then they can use MD to change
# their passwords.
# This will of course require them to enter the password that belongs to the Murmur account,
# and the accounts will only be linked if the password is correct.
# By default, this is enabled only for non-admin accounts, because if an admin account gets
# stolen they could easily take over the server. (So make sure the password can't be easily
# guessed, use at least over 9000 letters, blah blah.)
# This feature is only available if PROTECTED_MODE is not active.
ALLOW_ACCOUNT_LINKING = True		# Allow linking in general?
ALLOW_ACCOUNT_LINKING_ADMINS = False	# Allow linking for Admin accounts?

# Database settings for Mumble-Django's database. These do NOT need to point to Murmur's database,
# Mumble-Django should use its own!
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = join( MUMBLE_DJANGO_ROOT, 'mumble-django.db3' )
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''


# Show debug information on errors?
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True


# Absolute path to the directory that holds media.
MEDIA_ROOT = join( MUMBLE_DJANGO_ROOT, 'htdocs' )

# URL that handles the media served from MEDIA_ROOT.
MEDIA_URL = MUMBLE_DJANGO_URL+'static/'

# URL prefix for admin media -- CSS, JavaScript and images.
ADMIN_MEDIA_PREFIX = MUMBLE_DJANGO_URL+'media/'

# URL to the login view
LOGIN_URL = MUMBLE_DJANGO_URL + 'accounts/login';
LOGIN_REDIRECT_URL = MUMBLE_DJANGO_URL + 'accounts/profile';

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'u-mp185msk#z4%s(do2^5405)y5d!9adbn92)apu_p^qvqh10v'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.load_template_source',
	'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.locale.LocaleMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'pyweb.urls'

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	join( MUMBLE_DJANGO_ROOT, 'pyweb', 'templates' ),
)

TEMPLATE_CONTEXT_PROCESSORS = (
	"django.core.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	'processors.installed_apps',
)

TEST_RUNNER = 'mumble.testrunner.run_tests'
TEST_MURMUR_LAB_DIR   = join( dirname(MUMBLE_DJANGO_ROOT), 'murmur' );
TEST_MURMUR_FILES_DIR = join( MUMBLE_DJANGO_ROOT, 'testdata' );

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.admin',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'registration',
	'mumble',
)


def modprobe( name ):
	""" Try to import the named module, and if that works add it to INSTALLED_APPS. """
	global INSTALLED_APPS
	try:
		__import__( name )
	except ImportError:
		pass
	else:
		INSTALLED_APPS += ( name, )

# Check if rosetta is available.
#    http://code.google.com/p/django-rosetta
modprobe( "rosetta" )

# Check if django_extensions is available.
modprobe( "django_extensions" )
