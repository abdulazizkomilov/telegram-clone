from rest_framework.throttling import BaseThrottle
from django.core.cache import cache


class Throttle(BaseThrottle):
    rate_limit = 10
    period = 60

    def get_cache_key(self, request, view):
        return request.META.get("REMOTE_ADDR")

    def allow_request(self, request, view):
        cache_key = self.get_cache_key(request, view)
        request_count = cache.get(cache_key, 0)

        if request_count >= self.rate_limit:
            return False

        cache.set(cache_key, request_count + 1, timeout=self.period)
        return True
