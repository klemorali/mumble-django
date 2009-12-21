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

import os, subprocess, signal
from os.path		import join, exists
from shutil		import copyfile

from django.conf	import settings


def get_available_versions():
	""" Return murmur versions installed inside the LAB_DIR. """
	dirs = os.listdir( settings.TEST_MURMUR_LAB_DIR );
	dirs.sort();
	return dirs;


def run_callback( version, callback, *args, **kwargs ):
	""" Initialize the database and run murmur, then call the callback.
	    After the callback has returned, kill murmur.
	
	    The callback will be passed the Popen object that wraps murmur,
	    and any arguments that were passed to run_callback.
	
	    If the callback raises an exception, murmur will still be properly
	    shutdown and the exception will be reraised.
	
	    The callback can either return an arbitrary value, or a tuple.
	    If it returns a tuple, it must be of the form:
	
	        ( <any> intended_return_value, <bool> call_update_dbase )
	
	    That means: If the second value evaluates to True, update_dbase
	    will be called; the first value will be returned by run_callback.
	
	    If the callback returns anything other than a tuple, that value
	    will be returned directly.
	
	    So, If run_callback should return a tuple, you will need to return
	    the tuple form mentioned above in the callback, and put your tuple
	    into the first parameter.
	"""
	
	murmur_root = join( settings.TEST_MURMUR_LAB_DIR, version );
	if not exists( murmur_root ):
		raise EnvironmentError( "This version could not be found: '%s' does not exist!" % murmur_root );
	
	init_dbase( version );
	
	process = run_murmur( version );
	
	try:
		result = callback( process, *args, **kwargs );
	except Exception, err:
		raise err;
	else:
		if type(result) == tuple:
			if result[1]:
				update_dbase( version );
			return result[0];
		else:
			return result;
	finally:
		kill_murmur( process );


def init_dbase( version ):
	""" Initialize Murmur's database by copying the one from FILES_DIR. """
	dbasefile = join( settings.TEST_MURMUR_FILES_DIR, "murmur-%s.db3" % version );
	if not exists( dbasefile ):
		raise EnvironmentError( "This version could not be found: '%s' does not exist!" % dbasefile );
	murmurfile = join( settings.TEST_MURMUR_LAB_DIR, version, "murmur.sqlite" );
	copyfile( dbasefile, murmurfile );


def update_dbase( version ):
	""" Copy Murmur's database to FILES_DIR (the inverse of init_dbase). """
	murmurfile = join( settings.TEST_MURMUR_LAB_DIR, version, "murmur.sqlite" );
	if not exists( murmurfile ):
		raise EnvironmentError( "Murmur's database could not be found: '%s' does not exist!" % murmurfile );
	dbasefile = join( settings.TEST_MURMUR_FILES_DIR, "murmur-%s.db3" % version );
	copyfile( dbasefile, target );


def run_murmur( version ):
	""" Run the given Murmur version as a subprocess.
	
	    Either returns a Popen object or raises an EnvironmentError.
	"""
	
	murmur_root = join( settings.TEST_MURMUR_LAB_DIR, version );
	if not exists( murmur_root ):
		raise EnvironmentError( "This version could not be found: '%s' does not exist!" % murmur_root );
	
	binary_candidates = ( 'murmur.64', 'murmur.x86', 'murmurd' );
	
	files = os.listdir( murmur_root );
	
	for binname in binary_candidates:
		if exists( join( murmur_root, binname ) ):
			process = subprocess.Popen(
				( join( murmur_root, binname ), '-fg' ),
				stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
				cwd=murmur_root
				);
			return process;
	
	raise EnvironmentError( "Murmur binary not found. (Tried %s)" % unicode(binary_candidates) );


def kill_murmur( process ):
	""" Send a sigterm to the given process. """
	return os.kill( process.pid, signal.SIGTERM );


