from django import template
from django.urls import resolve, reverse, Resolver404
from django.utils import translation
from django.utils.text import slugify

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

    try:
        match = resolve(target_path)
    except Resolver404:
        return target_path

    translated_kwargs = {}
    for key, value in match.kwargs.items():
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

    query_string = request.META.get("QUERY_STRING", "")
    if query_string:
        url = f"{url}?{query_string}"

    return url