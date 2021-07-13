from functools import wraps
from urllib.parse import urlparse
import re

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url

from correspondence.models import Radicate

def has_any_permission(perms, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has at least some particular 
    permission enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """
    def check_perms(user):
        for perm in perms:
            if user.has_perm(perm):
                return True

        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        
        return False
    return user_passes_test(check_perms, login_url=login_url)

def user_passes_test_custom(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user, request):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator

def has_radicate_permission(perms, login_url=None, raise_exception=False):

    def check_perms(user, request):
        result = re.search(r'.*/radicate/(\d+)/', request.path, re.IGNORECASE)

        if user.has_perm('auth.receive_external') or user.is_superuser:
            return True

        if result:
            id = Radicate.objects.filter(
                        pk=int(result.group(1)), 
                        current_user_id=user.pk).values('current_user_id')
            if id:
                return True

        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        
        return False
    return user_passes_test_custom(check_perms, login_url=login_url)