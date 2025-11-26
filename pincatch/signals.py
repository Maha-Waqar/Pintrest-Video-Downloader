import os
import re
import shutil
import logging
from django.conf import settings
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django_restful_translator.translation_providers import TranslationProviderFactory
from pincatch.models import Page
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

# Minimal DeepL language normalization (align with blog signal mapping)
LANGUAGE_CODE_MAP = {
    'en': 'EN-US',
    'br': 'PT-BR',
    'pt': 'PT-PT',
    'de': 'DE',
    'es': 'ES',
    'fr': 'FR',
    'ru': 'RU',
    'ar': 'AR',
    'tr': 'TR',
    'id': 'ID',
    'it': 'IT',
    'uk': 'UK',
    'ko': 'KO',
    'ja': 'JA',
    'zh-hans': 'ZH',
}

RTL_LANGS = {
    'ar', 'ar-ye', 'ar-eg', 'ar-sa', 'fa', 'he', 'ur', 'ps'
}

@receiver(pre_save, sender=Page)
def remember_previous_template_path(sender, instance, **kwargs):
    """
    Store previous slug/language slug before saving so we can clean templates if needed.
    """
    if not instance.pk:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    instance._old_slug_url = previous.slug_url
    instance._old_language_slug = previous.get_language_slug()


@receiver(post_save, sender=Page)
def generate_page_templates(sender, instance, created, **kwargs):
    """
    Signal handler to automatically generate templates for Page instances
    """
    new_language_slug = instance.get_language_slug()
    template_slug_changed = (
        created
        or getattr(instance, "_old_slug_url", None) != instance.slug_url
        or getattr(instance, "_old_language_slug", None) != new_language_slug
    )
    if template_slug_changed:
        moved = False
        if not created:
            try:
                moved = _try_move_existing_template(instance)
            except Exception as exc:
                logger.warning(
                    "Failed to relocate template for page %s/%s: %s",
                    instance.slug_url,
                    instance.language,
                    exc,
                    exc_info=True,
                )
        try:
            if not moved:
                _generate_page_template(instance)
        except Exception as e:
            logger.error(
                "Error generating template for page %s/%s: %s",
                instance.slug_url,
                instance.language,
                e,
                exc_info=True,
            )
        old_slug = getattr(instance, "_old_slug_url", None)
        old_language_slug = getattr(instance, "_old_language_slug", None)
        if not moved and old_slug and old_language_slug and (old_slug != instance.slug_url or old_language_slug != new_language_slug):
            _remove_template_file(old_slug, old_language_slug)
    # Translation to other languages is triggered explicitly via admin actions, not automatically on save.

def _generate_page_template(page_instance):
    """
    Generate HTML template for a specific language
    """
    # Use default language code when language_slug is blank so templates have a concrete filename.
    language_slug = page_instance.get_language_slug() or settings.LANGUAGE_CODE
    template_dir, template_path = _get_template_paths(page_instance.slug_url, language_slug)

    # Create directory if it doesn't exist
    os.makedirs(template_dir, exist_ok=True)

    # Template content
    template_content = """{% extends "index.html" %}
{% load i18n %}

{% block title %}{{ meta_title }}{% endblock %}

{% block meta_description %}{{ meta_description }}{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-4xl mx-auto">
        <div class="prose prose-lg max-w-none">
            {{ content|safe }}
        </div>
    </div>
</div>
{% endblock %}
"""

    # Write the template file
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)

    logger.info(f"Generated template: {template_path}")


def _translate_page_to_other_languages(source_page, force_override=True):
    """
    Translate the default-language page into all configured languages, saving each Page record.
    Uses django_restful_translator providers already installed in the project.

    force_override=True will overwrite existing translated content (used on first create).
    force_override=False will backfill only empty fields to respect manual edits.
    """
    default_lang = settings.LANGUAGE_CODE
    if source_page.language != default_lang:
        return

    provider = _get_provider_safely()
    languages = [lang[0] for lang in settings.LANGUAGES if lang[0] != default_lang]

    for language in languages:
        target_page, _ = Page.objects.get_or_create(
            slug_url=source_page.slug_url,
            language=language,
            defaults={"group": source_page.group, "language_slug": language},
        )
        if not target_page.language_slug:
            target_page.language_slug = language
        target_page.is_homepage = source_page.is_homepage

        # Always overwrite translated fields from the English source so all languages stay in sync.
        target_page.name = _safe_translate(provider, source_page.name, default_lang, language)
        target_page.meta_title = _safe_translate(provider, source_page.meta_title, default_lang, language)
        target_page.meta_description = _safe_translate(provider, source_page.meta_description, default_lang, language)
        target_page.meta_keywords = _safe_translate(provider, source_page.meta_keywords, default_lang, language)
        target_page.head_html = _safe_translate(provider, source_page.head_html, default_lang, language)
        target_page.content = _safe_translate(provider, source_page.content, default_lang, language)

        target_page.save()


def _get_provider_safely():
    """Return translation provider if available; fallback to None if misconfigured."""
    try:
        return TranslationProviderFactory.get_provider('deepl')
    except ImproperlyConfigured:
        logger.warning("Translation provider misconfigured; falling back to source text.")
    except Exception as exc:
        logger.error(f"Failed to init translation provider: {exc}", exc_info=True)
    return None


def _safe_translate(provider, text, source_lang, target_lang):
    """Translate text; on any failure, return the original text so pages are still created."""
    if not text:
        return text
    if provider is None:
        return text
    if getattr(provider, "_disable_after_error", False):
        return text
    normalized_target = LANGUAGE_CODE_MAP.get(target_lang, target_lang)
    # Preserve HTML structure by translating only text nodes when markup is present.
    def _translate_html(html_text):
        try:
            from bs4 import BeautifulSoup
        except Exception:
            return None

        def _apply_rtl(soup_obj):
            block_tags = {"p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "div", "section", "article", "details", "summary"}
            for tag in soup_obj.find_all(block_tags):
                if not tag.has_attr("dir"):
                    tag["dir"] = "rtl"
                # Keep existing alignment; only set if none
                current_style = tag.get("style", "")
                if "text-align" not in current_style:
                    tag["style"] = (current_style + "; text-align: right;").strip("; ")

        def _preserve_whitespace(original, translated):
            match = re.match(r"(\s*)(.*?)(\s*)$", original, flags=re.DOTALL)
            if not match:
                return translated
            prefix, core, suffix = match.groups()
            return f"{prefix}{translated}{suffix}"

        try:
            from bs4 import Comment

            soup = BeautifulSoup(html_text, "html.parser")
            for node in soup.find_all(string=True):
                if isinstance(node, Comment):
                    # Preserve comments untouched so they don't become visible text after translation.
                    continue
                if getattr(node, "parent", None) and node.parent.name in {"script", "style"}:
                    continue
                original = str(node)
                if not original.strip():
                    continue
                try:
                    translated = provider.translate_text(original, source_lang, normalized_target)
                except Exception:
                    translated = original
                node.replace_with(_preserve_whitespace(original, translated))
            if normalized_target.lower() in RTL_LANGS:
                _apply_rtl(soup)
            return str(soup)
        except Exception:
            return None

    if "<" in text and ">" in text:
        translated_html = _translate_html(text)
        if translated_html is not None:
            return translated_html
    try:
        return provider.translate_text(text, source_lang, normalized_target)
    except Exception as exc:
        logger.error(
            "Translation failed for %s->%s: %s; using source text",
            source_lang,
            target_lang,
            exc,
            exc_info=True,
        )
        try:
            provider._disable_after_error = True  # Avoid hammering provider when failing (e.g., offline)
        except Exception:
            pass
        return text


def _remove_template_file(slug_url, language_slug):
    """Delete template file for a slug/language slug combo and clean empty dir."""
    if not slug_url or not language_slug:
        return
    template_dir, template_path = _get_template_paths(slug_url, language_slug)
    try:
        if os.path.isfile(template_path):
            os.remove(template_path)
            logger.info("Deleted template %s.", template_path)
    except OSError as exc:
        logger.warning("Failed to delete template %s: %s", template_path, exc, exc_info=True)

    _cleanup_template_dir(template_dir)


def _get_template_paths(slug_url, language_slug):
    """Return (directory, file path) for template storage."""
    template_dir = os.path.join(settings.BASE_DIR, 'templates', slug_url)
    template_path = os.path.join(template_dir, f"{language_slug}.html")
    return template_dir, template_path


def _cleanup_template_dir(template_dir):
    try:
        if os.path.isdir(template_dir) and not os.listdir(template_dir):
            os.rmdir(template_dir)
            logger.info("Removed empty template directory %s.", template_dir)
    except OSError as exc:
        logger.warning("Failed to remove template directory %s: %s", template_dir, exc, exc_info=True)


def _try_move_existing_template(instance):
    """Move old template file to the new slug path if it exists."""
    old_slug = getattr(instance, "_old_slug_url", None)
    old_language_slug = getattr(instance, "_old_language_slug", None)
    if not old_slug or not old_language_slug:
        return False

    old_dir, old_path = _get_template_paths(old_slug, old_language_slug)
    new_dir, new_path = _get_template_paths(instance.slug_url, instance.get_language_slug())
    if not os.path.isfile(old_path):
        return False

    os.makedirs(new_dir, exist_ok=True)
    shutil.move(old_path, new_path)
    logger.info("Moved template %s -> %s.", old_path, new_path)
    _cleanup_template_dir(old_dir)
    return True


@receiver(post_delete, sender=Page)
def delete_page_template(sender, instance, **kwargs):
    """
    Remove the generated template file (and empty directory) when a Page is deleted.
    """
    _remove_template_file(instance.slug_url, instance.get_language_slug())
