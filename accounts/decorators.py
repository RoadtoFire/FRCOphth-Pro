from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Subscription


def subscription_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            if request.user.subscription.is_valid:
                return view_func(request, *args, **kwargs)
        except Subscription.DoesNotExist:
            pass
        messages.warning(request, 'You need an active subscription to access this.')
        return redirect('choose_plan')
    return wrapper