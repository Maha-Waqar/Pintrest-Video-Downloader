import re
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from blog.models import Post

def index(request):
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='header:x-real-ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden', status=403)
        # ...existing logic...
        posts = Post.objects.all().order_by("-created_on").prefetch_related('translations')[:3]
        breadcrumbs = [{'title': 'Home', 'url': None}]
        return render(request, 'home.html', {'blogs': posts, 'breadcrumbs': breadcrumbs})
    return protected_home(request)

def imageDownload(request):
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='header:x-real-ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden', status=403)
        # ...existing logic...
        breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Image Downloader', 'url': None}]
        return render(request, 'image.html', {'breadcrumbs': breadcrumbs})
    return protected_home(request)

def gifDownload(request):
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='header:x-real-ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden', status=403)
        # ...existing logic...
        breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Gif Downloader', 'url': None}]
        return render(request, 'gif.html', {'breadcrumbs': breadcrumbs})
    return protected_home(request)

def is_valid_url(url):
    return re.match(r'^https?://(www\.)?pinterest\.com/', url)

def about(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'About', 'url': None}]
    return render(request, 'about.html', {'breadcrumbs': breadcrumbs})

def contactUs(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Contact Us', 'url': None}]
    return render(request, 'contactUs.html', {'breadcrumbs': breadcrumbs})

def privacyPolicy(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Privacy Policy', 'url': None}]
    return render(request, 'privacyPolicy.html', {'breadcrumbs': breadcrumbs})

def termsAndConditions(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Terms and Conditions', 'url': None}]
    return render(request, 'termsAndConditions.html', {'breadcrumbs': breadcrumbs})

def copyrightPolicy(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Copyright Policy', 'url': None}]
    return render(request, 'copyrightPolicy.html', {'breadcrumbs': breadcrumbs})
