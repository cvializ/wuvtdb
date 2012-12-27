import datetime
import socket
import sys
import traceback
import warnings
from hashlib import md5

import django.views.debug
from django.conf import settings
from django.http import Http404

from tbdblog.models import *

__all__ = ('DBLogMiddleware', 'DBLOG_CATCH_404_ERRORS')

DBLOG_CATCH_404_ERRORS = getattr(settings, 'DBLOG_CATCH_404_ERRORS', False)

class DBLogMiddleware(object):
    def process_exception(self, request, exception):
        if not DBLOG_CATCH_404_ERRORS and isinstance(exception, Http404):
            return
        server_name = socket.gethostname()
        tb_text     = traceback.format_exc()
        tb_html     = django.views.debug.technical_500_response(request, sys.exc_type,
                                                                sys.exc_value, sys.exc_traceback)

        class_name  = exception.__class__.__name__
        checksum    = md5(tb_text).hexdigest()

        defaults = dict(
            class_name  = class_name,
            url         = request.build_absolute_uri(),
            server_name = server_name,
            traceback   = tb_text,
            traceback_html = str(tb_html),
        )

        try:
            Error.objects.create(**defaults)
            defaults.__delitem__('traceback_html')
            batch, created = ErrorBatch.objects.get_or_create(
                class_name = class_name,
                server_name = server_name,
                checksum = checksum,
                defaults = defaults
            )
            if not created:
                batch.times_seen += 1
                batch.last_seen = datetime.datetime.now()
                batch.resolved = False
                batch.save()
        except Exception, exc:
            warnings.warn(unicode(exc))
