"""
URL configuration for pincatch project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns, set_language
from django.contrib.sitemaps.views import sitemap
from blog.sitemaps import StaticViewSitemap, PostSitemap, CategorySitemap, PinToolSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'posts': PostSitemap,
    'categories': CategorySitemap,
    'pin_tools': PinToolSitemap,
}

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('rosetta/', include('rosetta.urls')),
    path("about", views.about, name="about"),
    path("contact-us", views.contactUs, name="contactUs"),
    path("privacy-policy", views.privacyPolicy, name="privacyPolicy"),
    path("terms-and-conditions", views.termsAndConditions, name="termsAndConditions"),
    path("copyright-policy", views.copyrightPolicy, name="copyrightPolicy"),
    path('blog/', include('blog.urls')),
    path('i18n/setlang/', set_language, name='set_language'),
)
urlpatterns += [
    path("", views.index, name="home"),
    path("pinterest-image-downloader", views.imageDownload, name="imageDownloader"),
    path("pinterest-gif-downloader", views.gifDownload, name="gifDownloader"),
    path("pinterest-profile-picture-downloader", views.profileDownload, name="profileDownloader"),
    path('pin/', include('pincatch.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', views.robot , name='robot'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path("<slug:language_slug>/", views.localized_home, name="home_language"),
    path("<slug:language_slug>", views.localized_home, name="home_language_no_slash"),
    path("<slug:language_slug>/<slug:slug>/", views.page_view, name='page_view'),
    path("<slug:language_slug>/<slug:slug>", views.page_view, name='page_view_no_slash'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# No changes needed for CSRF, User-Agent, or rate limiting in urls.py itself.
# Just a comment for maintainability
# Only the protected views (with CSRF, ratelimit, and header checks) are exposed here.
# All protections are handled in the view functions themselves.
