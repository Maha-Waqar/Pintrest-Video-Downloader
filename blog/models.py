from django.db import models
from django_restful_translator.models import TranslatableModel
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField
from blog.translation_cleanup import build_slug_lookup, clean_translation_html
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.conf import settings


class Category(TranslatableModel):
    name = models.CharField(max_length=30, unique=True, default="None")
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    translatable_fields = ['name']

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_translated_name(self, language=None):
        """Get translated name for specified language or current language"""
        if language is None:
            from django.utils import translation
            language = translation.get_language()
        
        # Try to get from translations
        translation_obj = self.translations.filter(
            language=language, 
            field_name='name'
        ).first()
        if translation_obj:
            return translation_obj.field_value
        return self.name

class Post(TranslatableModel):
    title = models.CharField(max_length=255, default="No Title")
    body = RichTextUploadingField()
    meta_title = models.CharField(default="Meta Title")
    meta_description = models.TextField(default="Meta Description")
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("Category", related_name="posts")
    image = models.ImageField(upload_to="uploads/", null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, default="no-slug")

    # Add slug to translatable fields so each language can have a localized URL segment
    translatable_fields = ['title', 'body', 'slug']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)

    def get_translated_title(self, language=None):
        """Get translated title for specified language or current language"""
        if language is None:
            from django.utils import translation
            language = translation.get_language()
        
        # Try to get from translations
        translation_obj = self.translations.filter(
            language=language, 
            field_name='title'
        ).first()
        if translation_obj:
            return translation_obj.field_value
        return self.title

    def _normalize_translation_body(self, language: str, translated_html: str) -> str:
        slug_lookup = build_slug_lookup([self], language)
        return clean_translation_html(self.body, translated_html, slug_lookup)

    def get_translated_slug(self, language=None):
        """Return localized slug normalized for URLs or fallback to default slug."""
        if language is None:
            from django.utils import translation
            language = translation.get_language()
        default_language = settings.LANGUAGE_CODE

        translation_obj = self.translations.filter(
            language=language,
            field_name='slug'
        ).first()

        if translation_obj and translation_obj.field_value:
            normalized = slugify(translation_obj.field_value, allow_unicode=True)
            if normalized and translation_obj.field_value != normalized:
                translation_obj.field_value = normalized
                translation_obj.save(update_fields=['field_value'])
            if normalized:
                return normalized
            return translation_obj.field_value

        fallback_slug = getattr(self, 'slug', None)
        if language == default_language:
            return fallback_slug

        if fallback_slug:
            if translation_obj:
                if not translation_obj.field_value:
                    translation_obj.field_value = fallback_slug
                    translation_obj.save(update_fields=['field_value'])
            else:
                self.translations.create(
                    language=language,
                    field_name='slug',
                    field_value=fallback_slug
                )
        return fallback_slug
    
    def get_translated_body(self, language=None):
        """Get translated body for specified language or current language"""
        if language is None:
            from django.utils import translation
            language = translation.get_language()
        
        # Try to get from translations
        translation_obj = self.translations.filter(
            language=language, 
            field_name='body'
        ).first()
        if translation_obj:
            cleaned = self._normalize_translation_body(language, translation_obj.field_value)
            if cleaned != translation_obj.field_value:
                translation_obj.field_value = cleaned
                translation_obj.save(update_fields=['field_value'])
            return cleaned
        return self.body
    
    def has_translation_for_language(self, language):
        """
        Return True if the post has a translation stub in the specified language.
        """
        return self.translations.filter(
            language=language,
            field_name='title'
        ).exists()
