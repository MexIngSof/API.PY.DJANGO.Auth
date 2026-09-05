"""
ASGI config for auth project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os

from django.core.asgi import get_asgi_application

from .observability import ObservabilityMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = ObservabilityMiddleware(get_asgi_application())
