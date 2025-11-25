import re
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from django.utils import translation
from django.utils.translation import gettext as _
from blog.models import Post
from pincatch.models import Page
from pincatch.seo import build_seo_context

def _render_page_instance(request, page):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}]
    if page.slug_url == Page.HOME_SLUG:
        breadcrumbs[-1]['url'] = None
    else:
        breadcrumbs.append({'title': page.name, 'url': None})
    context = {
        'page_title': page.name,
        'meta_title': page.meta_title,
        'meta_description': page.meta_description,
        'content': page.content,
        'breadcrumbs': breadcrumbs,
    }
    # Surface latest blogs for dynamic home pages so templates can render them.
    if page.slug_url == Page.HOME_SLUG:
        context['blogs'] = Post.objects.all().order_by("-created_on").prefetch_related('translations')[:3]
    context.update(build_seo_context(request, page.meta_title, page.meta_description))
    lang_slug = page.get_language_slug() or settings.LANGUAGE_CODE
    template_name = f'{page.slug_url}/{lang_slug}.html'
    return render(request, template_name, context)


def _find_home_page_by_slug(language_slug):
    if not language_slug:
        return None
    return Page.objects.filter(is_homepage=True, language_slug=language_slug).first()


def _find_home_page_by_language(language_code):
    return Page.objects.filter(is_homepage=True, language=language_code).first()


def index(request, language_slug=None):
    target_page = None
    target_language = settings.LANGUAGE_CODE
    default_home = _find_home_page_by_language(settings.LANGUAGE_CODE)

    if language_slug:
        target_page = _find_home_page_by_slug(language_slug)
        if target_page:
            target_language = target_page.language
        elif language_slug in dict(settings.LANGUAGES):
            target_language = language_slug
            target_page = _find_home_page_by_language(target_language)
        else:
            target_page = default_home

        # If the requested slug doesn't match the canonical slug for the home page, issue a 301 to the canonical slug.
        if target_page:
            canonical_slug = target_page.get_language_slug()
            if canonical_slug != language_slug:
                # If canonical slug is empty, render at root instead of redirecting to a prefixed path.
                if canonical_slug == "":
                    response = redirect("home", permanent=True)
                    response["Cache-Control"] = "no-store"
                    return response
                else:
                    response = redirect("home_language", language_slug=canonical_slug, permanent=True)
                    response["Cache-Control"] = "no-store"
                    return response
    else:
        # Request to root; if default home has a custom language_slug (e.g., en or en1), redirect to it.
        if default_home and default_home.language_slug:
            # Use a permanent redirect so search engines treat the language slug URL as canonical.
            response = redirect("home_language", language_slug=default_home.language_slug, permanent=True)
            # Prevent long-lived client caching so an updated language slug takes effect immediately.
            response["Cache-Control"] = "no-store"
            return response
        target_page = default_home

    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='header:x-real-ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden', status=403)
        if target_page:
            translation.activate(target_language)
            request.LANGUAGE_CODE = target_language
            return _render_page_instance(request, target_page)
        # ...existing logic...
        posts = Post.objects.all().order_by("-created_on").prefetch_related('translations')[:3]
        breadcrumbs = [{'title': 'Home', 'url': None}]
        context = {
            'blogs': posts,
            'breadcrumbs': breadcrumbs,
        }
        context.update(build_seo_context(request))
        return render(request, 'home.html', context)
    return protected_home(request)


def localized_home(request, language_slug):
    return index(request, language_slug=language_slug)

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
        context = {
            'breadcrumbs': breadcrumbs,
        }
        context.update(build_seo_context(
            request,
            _("Pinterest Image Downloader - Save HD Photos from Pins"),
            _("Download Pinterest images in HD quality without installing any apps using PinCatch.")
        ))
        return render(request, 'image.html', context)
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
        context = {
            'breadcrumbs': breadcrumbs,
        }
        context.update(build_seo_context(
            request,
            _("Pinterest GIF Downloader - Save Animated Pins Online"),
            _("Convert and download Pinterest GIFs instantly in high quality with the free PinCatch GIF downloader.")
        ))
        return render(request, 'gif.html', context)
    return protected_home(request)

def profileDownload(request):
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='header:x-real-ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden', status=403)
        # ...existing logic...
        breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Profile Picture Downloader', 'url': None}]
        context = {
            'breadcrumbs': breadcrumbs,
        }
        context.update(build_seo_context(
            request,
            _("Pinterest URL Downloader - Save Animated Pins Online"),
            _("Convert and download Pinterest URLs instantly in high quality with the free PinCatch Url downloader.")
        ))
        return render(request, 'profile.html', context)
    return protected_home(request)

def is_valid_url(url):
    return re.match(r'^https?://(www\.)?pinterest\.com/', url)

def about(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'About', 'url': None}]
    context = {'breadcrumbs': breadcrumbs}
    context.update(build_seo_context(
        request,
        _("About PinCatch - Pinterest Video Downloader"),
        _("Learn more about the PinCatch downloader, our mission, and how we help creators save their favorite Pinterest content.")
    ))
    return render(request, 'about.html', context)

def contactUs(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Contact Us', 'url': None}]
    context = {'breadcrumbs': breadcrumbs}
    context.update(build_seo_context(
        request,
        _("Contact PinCatch Support"),
        _("Have questions about downloading Pinterest videos or removing content? Get in touch with the PinCatch support team.")
    ))
    return render(request, 'contactUs.html', context)

def privacyPolicy(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Privacy Policy', 'url': None}]
    context = {'breadcrumbs': breadcrumbs}
    context.update(build_seo_context(
        request,
        _("PinCatch Privacy Policy"),
        _("Understand how PinCatch processes downloader requests, what information we store, and how we protect user privacy.")
    ))
    return render(request, 'privacyPolicy.html', context)

def termsAndConditions(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Terms and Conditions', 'url': None}]
    context = {'breadcrumbs': breadcrumbs}
    context.update(build_seo_context(
        request,
        _("PinCatch Terms & Conditions"),
        _("Review the allowed usage of the PinCatch Pinterest downloader, copyright responsibilities, and legal terms.")
    ))
    return render(request, 'termsAndConditions.html', context)

def copyrightPolicy(request):
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Copyright Policy', 'url': None}]
    context = {'breadcrumbs': breadcrumbs}
    context.update(build_seo_context(
        request,
        _("PinCatch Copyright & Takedown Policy"),
        _("Report copyright concerns and see how PinCatch responds to DMCA takedowns for Pinterest videos, GIFs, and images.")
    ))
    return render(request, 'copyrightPolicy.html', context)

def robot(request):
    return render(request, 'robots.txt')

def page_view(request, language_slug, slug):
    """
    Dynamic view for handling all Page instances
    """
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='header:x-real-ip', rate='10/m', block=True)
    def protected_page_view(request, language_slug, slug):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden', status=403)

        # Get the page by group slug_url and language
        page = get_object_or_404(Page, slug_url=slug, language_slug=language_slug)
        return _render_page_instance(request, page)

    return protected_page_view(request, language_slug, slug)
