from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

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