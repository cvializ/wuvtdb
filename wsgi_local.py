import os, sys
sys.path.append('/srv/http/')
sys.path.append('/srv/http/wuvtdb')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wuvtdb.settings_local_production'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()