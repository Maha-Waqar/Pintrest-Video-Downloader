import re
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from blog.models import Post

def index(request):
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden: Suspicious User-Agent', status=403)
        # Referrer check (optional, can be commented out if not needed)
        referrer = request.META.get('HTTP_REFERER', '')
        if referrer and not referrer.startswith('http://127.0.0.1:8000'):
            return HttpResponse('Forbidden: Invalid Referrer', status=403)
        # Example: Validate input URL if present
        page_url = request.GET.get('url')
        if page_url and not is_valid_url(page_url):
            return HttpResponse('Invalid Pinterest URL', status=400)
        # ...existing logic...
        posts = Post.objects.all().order_by("-created_on").prefetch_related('translations')[:3]
        return render(request, 'home.html', {'blogs': posts})
    return protected_home(request)

def is_valid_url(url):
    return re.match(r'^https?://(www\.)?pinterest\.com/', url)

def about(request):
    return render(request, 'about.html')

def contactUs(request):
    return render(request, 'contactUs.html')

def privacyPolicy(request):
    return render(request, 'privacyPolicy.html')

def termsAndConditions(request):
    return render(request, 'termsAndConditions.html')

def copyrightPolicy(request):
    return render(request, 'copyrightPolicy.html')
