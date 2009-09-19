# -*- coding: utf-8 -*-

from server_detect		import find_existing_instances
from django.db.models		import signals
from mumble			import models

signals.post_syncdb.connect( find_existing_instances, sender=models );

