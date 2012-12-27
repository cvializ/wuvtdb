import os, sys
sys.path.append('/var/www/')
sys.path.append('/var/www/wuvtdb')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wuvtdb.settings_production'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
