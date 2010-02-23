#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 *  Copyright (C) 2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

DEFAULT_CONNSTRING = 'Meta:tcp -h 127.0.0.1 -p 6502'
DEFAULT_SLICEFILE  = '/usr/share/slice/Murmur.ice'

import os, sys
import inspect
import getpass

from optparse		import OptionParser
from mumble.mctl	import MumbleCtlBase

usage = """Usage: %prog [options] [<method name>] [<method arguments>]

Each method argument has the form: [<data type: bool|int|float|string>:]value

If you do not specify a data type, string will be assumed, otherwise
`value' will be converted to the given type first. The bool conversion
interprets each of 'True', 'true', '1', 'Yes', 'yes' as True, everything else
as False.

    Example: int:4 float:3.5 string:oh:hai foobar bool:yes"""

parser = OptionParser(usage=usage)

parser.add_option( "-d", "--django-settings",
	help="if specified, get connstring and slice defaults from the given Django "
	     "settings module. Default: empty.",
	default=None
	)

parser.add_option( "-c", "--connstring",
	help="connection string to use. Default is '%s'." % DEFAULT_CONNSTRING,
	default=None
	)

parser.add_option( "-i", "--icesecret",
	help="Ice secret to use in the connection. Also see --asksecret.",
	default=None
	)

parser.add_option( "-a", "--asksecret",
	help="Ask for the Ice secret on the shell instead of taking it from the command line.",
	action="store_true", default=False
	)

parser.add_option( "-s", "--slice",
	help="path to the slice file. Default is '%s'." % DEFAULT_SLICEFILE,
	default=None
	)

parser.add_option( "-e", "--encoding",
	help="Character set arguments are encoded in. Default: Read from LANG env variable with fallback to UTF-8.",
	default=None
	)

parser.add_option(
	"-v", "--verbose",
	help="Show verbose messages on stderr",
	default=False,
	action="store_true"
	)

options, progargs = parser.parse_args()

if options.django_settings is not None:
	if options.verbose:
		print >> sys.stderr, "Reading settings from module '%s'." % options.django_settings
	
	os.environ['DJANGO_SETTINGS_MODULE'] = options.django_settings
	from django.conf import settings
	
	if options.connstring is None:
		if options.verbose:
			print >> sys.stderr, "Setting connstring from settings module"
		options.connstring = settings.DEFAULT_CONN
	
	if options.slice is None:
		if options.verbose:
			print >> sys.stderr, "Setting slice from settings module"
		options.slice = settings.SLICE
else:
	if options.connstring is None:
		if options.verbose:
			print >> sys.stderr, "Setting default connstring"
		options.connstring = DEFAULT_CONNSTRING
	
	if options.slice is None:
		if options.verbose:
			print >> sys.stderr, "Setting default slice"
		options.slice = DEFAULT_SLICEFILE


if options.encoding is None:
	try:
		locale = os.environ['LANG']
		_, options.encoding = locale.split('.')
	except (KeyError, ValueError):
		options.encoding = "UTF-8"


if options.verbose:
	print >> sys.stderr, "Connection info:"
	print >> sys.stderr, "    Connstring: %s" % options.connstring
	print >> sys.stderr, "    Slice:      %s" % options.slice
	print >> sys.stderr, "Encoding:       %s" % options.encoding

if options.asksecret or options.icesecret == '':
	options.icesecret = getpass.getpass( "Ice secret: " )

ctl = MumbleCtlBase.newInstance( options.connstring, options.slice, options.icesecret )


if not progargs:
	# Print available methods.
	for method in inspect.getmembers( ctl ):
		if method[0][0] == '_' or not callable( method[1] ):
			continue
		
		if hasattr( method[1], "innerfunc" ):
			args = inspect.getargspec( method[1].innerfunc )[0]
		else:
			args = inspect.getargspec( method[1] )[0]
		
		if len( args ) > 1:
			if args[0] == 'self':
				print "%s( %s )" % ( method[0], ', '.join( args[1:] ) )
		else:
			print "%s()" % method[0]

else:
	# function name given. check if its args matches ours, if yes call it, if not print usage
	if options.verbose:
		print >> sys.stderr, "Method name:    %s" % progargs[0]
	
	method = getattr( ctl, progargs[0] )
	if hasattr( method, "innerfunc" ):
		method = method.innerfunc
	
	args = inspect.getargspec( method )[0]
	
	if len(progargs) == len(args) and args[0] == 'self':
		if len(args) == 1:
			print method(ctl)
		else:
			cleanargs = []
			for param in progargs[1:]:
				try:
					argtype, argval = param.split(':', 1)
				except ValueError:
					cleanargs.append( param.decode(options.encoding) )
				else:
					cleanval = {
					  'bool':   lambda val: val in ('True', 'true', '1', 'Yes', 'yes'),
					  'int':    int,
					  'float':  float,
					  'string': str
					  }[ argtype ]( argval )
					
					if argtype == 'string':
						cleanval = cleanval.decode(options.encoding)
					cleanargs.append(cleanval)
			
			if options.verbose:
				print >> sys.stderr, "Call arguments: %s" % repr(cleanargs)
			
			print method( ctl, *cleanargs )
	
	elif len(args) == 1:
		print >> sys.stderr, "Method '%s' does not take any arguments." % progargs[0]
		print >> sys.stderr, "Expected %s()" % progargs[0]
	
	else:
		print >> sys.stderr, "Invalid arguments for method '%s': %s" % ( progargs[0], ', '.join( progargs[1:] ) )
		print >> sys.stderr, "Expected %s( %s )" % ( progargs[0], ', '.join( args[1:] ) )

