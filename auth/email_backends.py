from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class DeferredExternalEmailBackend(BaseEmailBackend):
    """Keep runtime available while rejecting uncertified email delivery."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        raise ImproperlyConfigured(
            "AWS SES is DEFERRED_EXTERNAL; email delivery is unavailable until provider certification."
        )
