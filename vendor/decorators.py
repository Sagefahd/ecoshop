from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def vendor_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_vendor:
            messages.error(request, "You need a vendor account to access the dashboard.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return wrapper
