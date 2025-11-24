from django import template
from django.urls import reverse
from django.utils import translation
from django.conf import settings

from pincatch.models import Page

register = template.Library()


def _find_page(slug_url, language_code):
    language_page = (
        Page.objects.filter(slug_url=slug_url, language_slug=language_code)
        .only("slug_url", "language_slug")
        .first()
    )
    if language_page:
        return language_page
    default_page = (
        Page.objects.filter(slug_url=slug_url, language=settings.LANGUAGE_CODE)
        .only("slug_url", "language_slug")
        .first()
    )
    return default_page


@register.simple_tag
def page_url(slug_url, fallback_name=None):
    """
    Resolve the URL for a dynamic Page by slug url.
    Optionally fall back to reversing a named URL if the Page doesn't exist.
    """
    language_code = translation.get_language()
    page = _find_page(slug_url, language_code)
    if page:
        return reverse(
            "page_view",
            kwargs={"language_slug": page.get_language_slug(), "slug": page.slug_url},
        )
    if fallback_name:
        try:
            return reverse(fallback_name)
        except Exception:
            pass
    return "#"
