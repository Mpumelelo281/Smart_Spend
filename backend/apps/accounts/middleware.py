"""Stashes (user, ip_address) somewhere audit-log writers can reach it
without every call site having to accept and forward the request object.
"""

import threading

_local = threading.local()


def get_audit_context():
    return getattr(_local, "user", None), getattr(_local, "ip_address", None)


class AuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, "user", None)
        _local.ip_address = self._client_ip(request)
        try:
            return self.get_response(request)
        finally:
            _local.user = None
            _local.ip_address = None

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
