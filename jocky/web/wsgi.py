"""WSGI config for JOCKY Command Console."""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jocky.web.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
