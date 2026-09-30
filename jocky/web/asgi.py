"""ASGI configuration for JOCKY Command Console with Django Channels."""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from . import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jocky.web.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        re_path(r"^ws/status/(?P<case_id>[^/]+)/$", consumers.StatusConsumer.as_asgi()),
    ]),
})
