# import absolute imports from the future, so that our celery.py module won’t clash with the library:
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

import logging
from celery.signals import after_setup_logger

# set the default DJANGO_SETTINGS_MODULE environment variable for the celery command-line program:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idp3_async_api_djproj.settings')

# instance of class Celery:
celery_app = Celery('idp3_async_api_djproj')   ### django project folder needed as parameter
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Looks up for task modules in Django applications and loads them 
# app.autodiscover_tasks() tries to discover a file named task.py in all of our Django applications.
#celery_app.autodiscover_tasks(settings.INSTALLED_APPS)    # This way we shouldn’t have to manually add the individual modules to the CELERY_IMPORTS setting.
celery_app.autodiscover_tasks()
# ANOTHER OPTION:
#app.autodiscover_tasks(lambda : settings.INSTALLED_APPS)

# Suppress the debug logging shown below, while keeping warnings and errors
# [...DEBUG/MainProcess] Failed to enable maintenance notifications: unknown subcommand 'MAINT_NOTIFICATIONS'. Try CLIENT HELP.
# (With redis-py 8.1.0, this particular message is logged at DEBUG level)
@after_setup_logger.connect
def configure_redis_logging(**kwargs):
    logging.getLogger("redis.connection").setLevel(logging.WARNING)

# The debug_task example is a task that dumps its own request information. 
# Using the bind=True task option to easily refer to the current task instance.
#@celery_app.task(bind=True)
#def debug_task(self):
#    print('Request: {0!r}'.format(self.request))
