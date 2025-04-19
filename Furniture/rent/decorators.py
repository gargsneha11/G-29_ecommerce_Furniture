from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def buyer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        if request.user.role != 'buyer':
            messages.error(request, 'Only buyers can access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        if request.user.role != 'seller':
            messages.error(request, 'Only sellers can access this page.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 