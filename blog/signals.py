import logging
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from concurrent.futures import ThreadPoolExecutor

from blog.models import Post, Category
from blog.translation_cleanup import build_slug_lookup, clean_translation_html
from django.utils.text import slugify
from django_restful_translator.models import Translation
from django_restful_translator.processors.model import TranslationModelProcessor
from django_restful_translator.processors.translation_service import TranslationService
from django_restful_translator.translation_providers import TranslationProviderFactory
from django_restful_translator.utils import handle_futures

logger = logging.getLogger(__name__)


# Mapping for Django language codes to DeepL language codes
# NOTE: DeepL supports a limited set of languages. Unsupported languages will be skipped.
# See: https://developers.deepl.com/docs/getting-started/supported-languages
LANGUAGE_CODE_MAP = {
    'en': 'EN-US',      # English (US) - SUPPORTED
    'bn': None,         # Bengali - NOT SUPPORTED by DeepL
    'fr': 'FR',         # French - SUPPORTED
    'de': 'DE',         # German - SUPPORTED
    'es': 'ES',         # Spanish - SUPPORTED
    'pt': 'PT-PT',      # Portuguese (Portugal) - SUPPORTED
    'ru': 'RU',         # Russian - SUPPORTED
    'zh_CN': 'ZH',      # Chinese (Simplified) - SUPPORTED
    'zh_TW': 'ZH',      # Chinese (Traditional) - SUPPORTED
    'ja': 'JA',         # Japanese - SUPPORTED
    'ko': 'KO',         # Korean - SUPPORTED
    'it': 'IT',         # Italian - SUPPORTED
    'tr': 'TR',         # Turkish - SUPPORTED
    'ar': 'AR',         # Arabic - SUPPORTED
    'vi': None,         # Vietnamese - NOT SUPPORTED by DeepL
    'id': 'ID',         # Indonesian - SUPPORTED
    'az': None,         # Azerbaijani - NOT SUPPORTED by DeepL
    'br': 'PT-BR',      # Brazilian Portuguese - SUPPORTED
}


def normalize_language_code(lang_code):
    """
    Convert Django language codes to DeepL format.
    DeepL API requires specific formats like 'EN-US' instead of 'en'.
    Returns None if the language is not supported by DeepL.
    """
    # Try direct mapping first
    if lang_code in LANGUAGE_CODE_MAP:
        result = LANGUAGE_CODE_MAP[lang_code]
        if result is None:
            logger.warning(f"Language code '{lang_code}' is not supported by DeepL API")
        return result
    
    # Try case-insensitive lookup
    for key, value in LANGUAGE_CODE_MAP.items():
        if key.lower() == lang_code.lower():
            if value is None:
                logger.warning(f"Language code '{lang_code}' is not supported by DeepL API")
            return value
    
    # Fallback: return None for unmapped codes (assume unsupported)
    logger.warning(f"Language code '{lang_code}' not in map and will be skipped")
    return None


def translate_model_instance(instance, model_class, reset_existing=False):
    """
    Translate a saved model instance to all configured languages except the default language
    """
    try:
        logger.info(f"translate_model_instance called for {model_class.__name__} {instance.pk}")
        default_language = settings.LANGUAGE_CODE
        logger.info(f"Default language: {default_language}")
        available_languages = [lang[0] for lang in settings.LANGUAGES]
        logger.info(f"Available languages: {available_languages}")
        translatable_fields = getattr(model_class, 'translatable_fields', [])
        logger.info(f"Translatable fields: {translatable_fields}")
        
        if not translatable_fields:
            logger.warning(f"No translatable fields defined for {model_class.__name__}")
            return
        
        content_type = ContentType.objects.get_for_model(model_class)
        logger.info(f"Content type: {content_type}")
        
        for target_language in available_languages:
            if target_language == default_language:
                logger.info(f"Skipping default language: {default_language}")
                continue
            
            for field_name in translatable_fields:
                translation_obj = Translation.objects.filter(
                    content_type=content_type,
                    object_id=instance.pk,
                    language=target_language,
                    field_name=field_name
                ).first()

                original_value = getattr(instance, field_name, '')

                if reset_existing and translation_obj:
                    if original_value:
                        if translation_obj.field_value:
                            logger.info(f"Resetting translation for {field_name} in {target_language}")
                            translation_obj.field_value = ''
                            translation_obj.save(update_fields=['field_value'])
                        else:
                            logger.info(f"Translation for {field_name} in {target_language} already pending translation")
                    else:
                        logger.warning(f"Field {field_name} has no value")
                    continue

                if not translation_obj:
                    if original_value:
                        logger.info(f"Creating translation placeholder for {field_name} in {target_language}")
                        Translation.objects.create(
                            content_type=content_type,
                            object_id=instance.pk,
                            language=target_language,
                            field_name=field_name,
                            field_value=''  # Empty placeholder so the provider will populate it
                        )
                        logger.info("Translation placeholder created successfully")
                    else:
                        logger.warning(f"Field {field_name} has no value")
                    continue

                if translation_obj.field_value:
                    logger.info(f"Translation already exists for {field_name} in {target_language}")
                else:
                    logger.info(f"Translation for {field_name} in {target_language} already pending translation")

    except Exception as e:
        logger.error(f"Error during translate_model_instance: {e}", exc_info=True)


class NormalizedTranslationService(TranslationService):
    """
    Custom TranslationService that normalizes language codes to DeepL format.
    DeepL API requires codes like 'EN-US' instead of 'en'.
    
    Each instance is created with a SPECIFIC TARGET LANGUAGE (normalized).
    The parent class uses self.target_language for all translations, so we MUST
    pass the correctly normalized target language at initialization.
    """
    def __init__(self, provider, target_language_django):
        # Normalize the target language code for DeepL
        normalized_target = normalize_language_code(target_language_django)
        self.original_target_language = target_language_django
        logger.info(f"Creating translation service for {target_language_django} (DeepL code: {normalized_target})")
        # Pass the normalized target language to parent
        super().__init__(provider, normalized_target)
    
    def translate_item(self, translation):
        """
        Translate a single translation object.
        The parent class will use self.target_language (which is already normalized).
        We just need to restore the original Django language code after translation.
        """
        try:
            # Call parent's translate_item - it will translate using self.target_language (normalized)
            result = super().translate_item(translation)
            
            # Restore original Django language code and save
            if self.target_language != self.original_target_language:
                logger.info(f"Restoring original language code: {self.target_language} -> {self.original_target_language}")
                translation.language = self.original_target_language
                translation.save()
            
            return result
        except Exception as e:
            logger.error(f"Error in NormalizedTranslationService.translate_item: {e}", exc_info=True)
            raise


def translate_with_provider(instance, model_class, provider_name='deepl'):
    """
    Translate the model instance using the specified provider
    """
    try:
        logger.info(f"translate_with_provider called for {model_class.__name__} {instance.pk} with provider: {provider_name}")
        
        default_language = settings.LANGUAGE_CODE
        available_languages = [lang[0] for lang in settings.LANGUAGES]
        translatable_fields = getattr(model_class, 'translatable_fields', [])
        
        if not translatable_fields:
            logger.warning(f"No translatable fields for {model_class.__name__}")
            return
        
        content_type = ContentType.objects.get_for_model(model_class)
        
        # Get the provider
        logger.info(f"Getting provider: {provider_name}")
        provider = TranslationProviderFactory.get_provider(provider_name)
        logger.info(f"Provider obtained: {provider}")
        
        # Collect translations to translate
        translations_to_translate = []
        
        for target_language in available_languages:
            if target_language == default_language:
                continue
            
            for field_name in translatable_fields:
                translation_obj = Translation.objects.filter(
                    content_type=content_type,
                    object_id=instance.pk,
                    language=target_language,
                    field_name=field_name
                ).first()
                
                if translation_obj and not translation_obj.field_value:
                    translations_to_translate.append(translation_obj)
                    logger.info(f"Found translation to translate: {field_name} in {target_language}")
        
        logger.info(f"Total translations to translate: {len(translations_to_translate)}")
        
        if translations_to_translate:
            logger.info(f"Starting translation with provider")
            
            futures = []
            services_by_language = {}
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                for translation in translations_to_translate:
                    target_lang = translation.language
                    
                    # Check if this language is supported by DeepL
                    normalized_lang = normalize_language_code(target_lang)
                    if normalized_lang is None:
                        logger.warning(f"Skipping translation for {translation.field_name} in {target_lang} (not supported by DeepL)")
                        continue
                    
                    # Create a new service instance for this target language if we don't have one
                    if target_lang not in services_by_language:
                        logger.info(f"Creating translation service for target language: {target_lang}")
                        services_by_language[target_lang] = NormalizedTranslationService(provider, target_lang)
                    
                    service = services_by_language[target_lang]
                    logger.info(f"Submitting translation job for {translation.field_name} in {translation.language}")
                    futures.append(
                        executor.submit(service.translate_item, translation)
                    )
            
            # Wait for all translations to complete
            for i, future in enumerate(futures, 1):
                try:
                    result = future.result()
                    logger.info(f"Translation job {i} completed successfully")
                except Exception as e:
                    logger.error(f"Translation error on job {i}: {e}", exc_info=True)
        else:
            logger.info(f"No translations to translate")
    
    except Exception as e:
        logger.error(f"Error during translate_with_provider: {e}", exc_info=True)


def _ensure_translated_slugs(post: Post) -> None:
    """Derive localized slugs from translated titles for every active language."""
    default_language = settings.LANGUAGE_CODE
    target_languages = [lang for lang, _ in settings.LANGUAGES if lang != default_language]

    for language in target_languages:
        try:
            derived_slug = post.get_translated_slug(language=language)
            if derived_slug:
                logger.info(
                    "Post %s slug for %s ensured via title-derived slug: %s",
                    post.pk,
                    language,
                    derived_slug,
                )
                continue

            translation_obj = post.translations.filter(
                language=language,
                field_name='slug'
            ).first()

            fallback_slug = slugify(post.title, allow_unicode=True) or post.slug
            if translation_obj:
                translation_obj.field_value = fallback_slug
                translation_obj.save(update_fields=['field_value'])
            else:
                post.translations.create(
                    language=language,
                    field_name='slug',
                    field_value=fallback_slug
                )
            logger.warning(
                "Post %s slug for %s fell back to default-language slug: %s",
                post.pk,
                language,
                fallback_slug,
            )
        except Exception as exc:
            logger.error(
                "Failed to ensure slug translation for Post %s language %s: %s",
                post.pk,
                language,
                exc,
                exc_info=True,
            )


def _post_translation_cleanup(post: Post) -> None:
    """Normalize translated body HTML immediately after translation."""
    translations = post.translations.filter(field_name='body').exclude(field_value="")
    if not translations.exists():
        return

    source_body = post.body
    all_posts = Post.objects.all().prefetch_related("translations")

    for translation_obj in translations:
        language = translation_obj.language
        slug_lookup = build_slug_lookup(all_posts, language)
        cleaned = clean_translation_html(source_body, translation_obj.field_value, slug_lookup)
        if cleaned != translation_obj.field_value:
            translation_obj.field_value = cleaned
            translation_obj.save(update_fields=["field_value"])
            logger.info(
                "Post %s translation for %s normalized during post-save cleanup",
                post.pk,
                language,
            )


def _do_post_translation(post_id, reset_existing=False):
    """
    Deferred translation task for Post - called after transaction commits
    """
    try:
        post = Post.objects.get(pk=post_id)
        state = "UPDATED" if reset_existing else "NEW"
        print(f"✓ Post {post_id} is {state}. Starting translation...")
        logger.info(f"Post {post_id} is {state}. Starting translation...")
        translate_model_instance(post, Post, reset_existing=reset_existing)
        logger.info(f"Translation objects prepared for Post {post_id}")
        translate_with_provider(post, Post, provider_name='deepl')
        logger.info(f"Translation completed for Post {post_id}")
        _ensure_translated_slugs(post)
        _post_translation_cleanup(post)
    except Exception as e:
        print(f"❌ Post translation failed: {e}")
        logger.error(f"Post translation failed: {e}", exc_info=True)


def _do_category_translation(category_id, reset_existing=False):
    """
    Deferred translation task for Category - called after transaction commits
    """
    try:
        category = Category.objects.get(pk=category_id)
        state = "UPDATED" if reset_existing else "NEW"
        print(f"✓ Category {category_id} is {state}. Starting translation...")
        logger.info(f"Category {category_id} is {state}. Starting translation...")
        translate_model_instance(category, Category, reset_existing=reset_existing)
        logger.info(f"Translation objects prepared for Category {category_id}")
        translate_with_provider(category, Category, provider_name='deepl')
        logger.info(f"Translation completed for Category {category_id}")
    except Exception as e:
        print(f"❌ Category translation failed: {e}")
        logger.error(f"Category translation failed: {e}", exc_info=True)
