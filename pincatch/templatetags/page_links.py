from django import template
from django.conf import settings
from django.template import engines
from django.urls import reverse
from django.utils import translation
from django.utils.safestring import mark_safe

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


@register.simple_tag(takes_context=True)
def render_page_content(context, content):
    """
    Render stored Page.content through the Django template engine so template
    tags like `page_url` inside rich text are evaluated.
    """
    if not content:
        return ""

    # Preload commonly used libraries so rich text snippets can call them
    # without needing explicit `{% load %}` statements.
    template_source = "{% load page_links i18n static %}" + str(content)
    try:
        template_obj = engines["django"].from_string(template_source)
        rendered = template_obj.render(context.flatten())
        return mark_safe(rendered)
    except Exception:
        # If anything goes wrong, fall back to the original content rather
        # than breaking the page rendering.
        return mark_safe(content)
