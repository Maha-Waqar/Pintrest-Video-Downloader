from django import template
from django.conf import settings
from django.urls import resolve, reverse, Resolver404
from django.utils import translation
from django.utils.text import slugify
from pincatch.models import Page

register = template.Library()



def _normalize_slug(value):
    if value is None:
        return value
    normalized = slugify(str(value), allow_unicode=True)
    return normalized or str(value)


def _translate_argument(value, language):
    """Return the translated version of a value if available."""
    translate_attr = getattr(value, "get_translated_slug", None)
    if translate_attr:
        return translate_attr(language=language)
    translate_attr = getattr(value, "get_translated_name", None)
    if translate_attr:
        return translate_attr(language=language)
    return value


def _translate_page_view(match, language_code):
    """
    Return kwargs for the dynamic Page view in the target language.
    """
    slug = match.kwargs.get("slug")
    if not slug:
        return {}
    try:
        page = (
            Page.objects.filter(slug_url=slug, language=language_code)
            .only("slug_url", "language_slug")
            .first()
        )
    except Exception:
        page = None
    if page:
        return {
            "slug": page.slug_url,
            "language_slug": page.get_language_slug(),
        }
    fallback_language_slug = match.kwargs.get("language_slug") or language_code
    return {"slug": slug, "language_slug": fallback_language_slug}


def _get_home_language_slug(language_code):
    if language_code == settings.LANGUAGE_CODE:
        return None
    page = (
        Page.objects.filter(is_homepage=True, language=language_code)
        .only("language_slug")
        .first()
    )
    if page:
        return page.get_language_slug()
    return language_code


@register.simple_tag(takes_context=True)
def translate_url(context, language_code, target=None):
    request = context["request"]
    current_language = translation.get_language()

    if target is None:
        target_path = request.path_info
    elif hasattr(target, "path_info"):
        target_path = target.path_info
    else:
        target_path = str(target)

    query_string = request.META.get("QUERY_STRING", "")

    try:
        match = resolve(target_path)
    except Resolver404:
        return target_path

    if match.view_name in {"home", "home_language", "home_language_no_slash"}:
        translation.activate(language_code)
        try:
            if language_code == settings.LANGUAGE_CODE:
                url = reverse("home")
            else:
                target_slug = _get_home_language_slug(language_code) or language_code
                url = reverse("home_language", kwargs={"language_slug": target_slug})
        finally:
            translation.activate(current_language)
        if query_string:
            url = f"{url}?{query_string}"
        return url

    translated_kwargs = {}
    page_specific_kwargs = None
    if match.view_name == "page_view":
        page_specific_kwargs = _translate_page_view(match, language_code)

    for key, value in match.kwargs.items():
        if page_specific_kwargs and key in page_specific_kwargs:
            translated_kwargs[key] = page_specific_kwargs[key]
            continue
        if key in context:
            translated_value = _translate_argument(context[key], language_code)
            if key == "slug":
                translated_value = _normalize_slug(translated_value)
            translated_kwargs[key] = translated_value
        elif key == "slug" and "blog" in context:
            translated_slug = context["blog"].get_translated_slug(language_code)
            translated_kwargs[key] = _normalize_slug(translated_slug)
        elif key == "category" and "category" in context:
            translated_kwargs[key] = context["category"].get_translated_name(language_code)
        else:
            translated_value = _translate_argument(value, language_code)
            if key == "slug":
                translated_value = _normalize_slug(translated_value)
            translated_kwargs[key] = translated_value

    translation.activate(language_code)
    try:
        url = reverse(match.view_name, args=match.args, kwargs=translated_kwargs)
    finally:
        translation.activate(current_language)

    if query_string:
        url = f"{url}?{query_string}"

    return url
