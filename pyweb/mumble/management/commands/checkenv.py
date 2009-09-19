# -*- coding: utf-8 -*-

import os

from django.core.management.base	import BaseCommand
from django.contrib.auth.models 	import User
from django.contrib.sites.models	import Site
from django.conf			import settings

from mumble.models			import Mumble

class TestFailed( Exception ):
	pass;

class Command( BaseCommand ):
	def handle(self, **options):
		self.check_dbase();
		self.check_sites();
		self.check_mumbles();
		self.check_admins();
	
	
	def check_dbase( self ):
		print "Checking database access...",
		if settings.DATABASE_ENGINE == "sqlite3":
			if not os.path.exists( settings.DATABASE_NAME ):
				raise TestFailed( "database does not exist. Have you run syncdb yet?" );
			
			else:
				statinfo = os.stat( settings.DATABASE_NAME );
				
				if statinfo.st_uid == 0:
					raise TestFailed( ""
						"the database file belongs to root. This is most certainly not what "
						"you want because it will prevent your web server from being able "
						"to write to it. Please check." );
				
				elif not os.access( settings.DATABASE_NAME, os.W_OK ):
					raise TestFailed( "database file is not writable." );
				
				else:
					print "[ OK ]";
		
		else:
			print "not using sqlite, so I can't check.";
	
	
	def check_sites( self ):
		print "Checking URL configuration...",
		
		site = Site.objects.get_current();
		if site.domain == 'example.com':
			print(  "The domain is configured as example.com, which is the default but does not make sense."
				"Please enter the domain where Mumble-Django is reachable." );
			
			site.domain = raw_input( "> " ).strip();
			site.save();
		
		else:
			print site.domain, "[ OK ]";
	
	
	def check_admins( self ):
		print "Checking if an Admin user exists...",
		
		for user in User.objects.all():
			if user.is_superuser:
				print "[ OK ]";
				return;
		
		raise TestFailed( ""
			"No admin user exists, so you won't be able to log in to the admin system. You "
			"should run `./manage.py createsuperuser` to create one." );
	
	
	def check_mumbles( self ):
		print "Checking Murmur instances...",
		
		mm = Mumble.objects.all();
		
		if mm.count() == 0:
			raise TestFailed( ""
				"no Mumble servers are configured, you might want to run "
				"`./manage.py syncdb` to run an auto detection." );
		
		else:
			for mumble in mm:
				try:
					ctl = mumble.ctl;
				except Exception, err:
					raise TestFailed(
						"Connecting to Murmur `%s` (%s) failed: %s" % ( mumble.name, mumble.dbus, err )
						);
			print "[ OK ]";






