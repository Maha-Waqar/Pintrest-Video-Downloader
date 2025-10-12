"""
URL configuration for pinit project.

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
import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns, set_language

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('rosetta/', include('rosetta.urls')),
    path("", views.index, name="home"),
    path('blogs/', include('blog.urls')),
    path('i18n/setlang/', set_language, name='set_language'),
)
urlpatterns += [
    path('pin/', include('pinit.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# No changes needed for CSRF, User-Agent, or rate limiting in urls.py itself.
# Just a comment for maintainability
# Only the protected views (with CSRF, ratelimit, and header checks) are exposed here.
# All protections are handled in the view functions themselves.
