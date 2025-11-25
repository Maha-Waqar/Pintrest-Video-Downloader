from django.db import models
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError

class PageGroup(models.Model):
    """Groups pages by slug_url across languages"""
    slug_url = models.CharField(max_length=255, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug_url

    def get_display_name(self):
        """Get a display name from the English page or first available"""
        english_page = self.pages.filter(language='en').first()
        if english_page:
            return english_page.name
        # Fallback to any page
        first_page = self.pages.first()
        return first_page.name if first_page else self.slug_url

class Page(models.Model):
    HOME_SLUG = "home"

    name = models.CharField(max_length=255, default="No Title")
    meta_title = models.CharField(default="Meta Title")
    meta_description = models.TextField(default="Meta Description")
    content = RichTextUploadingField()
    slug_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Path component without language, e.g., 'url-downloader'. Leave empty for homepage.",
    )
    language_slug = models.CharField(
        max_length=50,
        blank=True,
        help_text="Final URL segment for this page's language (defaults to the language code).",
    )
    language = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        help_text="Language for this page instance."
    )
    group = models.ForeignKey(PageGroup, related_name='pages', on_delete=models.CASCADE, null=True, blank=True)
    is_homepage = models.BooleanField(
        default=False,
        help_text="If enabled, this page will render at the root URL for the selected language.",
    )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('slug_url', 'language')
        constraints = [
            models.UniqueConstraint(fields=['slug_url', 'language_slug'], name='uniq_page_url_per_language_slug')
        ]

    def __str__(self):
        return f"{self.name} ({self.language})"

    def clean(self):
        if self.language not in [lang[0] for lang in settings.LANGUAGES]:
            raise ValidationError(f"Language {self.language} is not supported")
        normalized_slug = (self.slug_url or "").strip().strip('/')
        if self.is_homepage:
            self.slug_url = self.HOME_SLUG
        elif normalized_slug:
            if '/' in normalized_slug:
                normalized_slug = normalized_slug.split('/')[0]
            self.slug_url = normalized_slug
        else:
            raise ValidationError("Slug URL cannot be empty unless this is the homepage.")

    def save(self, *args, **kwargs):
        self.clean()
        if not self.language_slug:
            if self.is_homepage and self.language == settings.LANGUAGE_CODE:
                # Leave blank to keep default language at root when desired.
                self.language_slug = ""
            else:
                self.language_slug = self.language
        super().save(*args, **kwargs)
        if self.group_id:
            PageGroup.objects.filter(pk=self.group_id).update(slug_url=self.slug_url)

    def get_language_slug(self):
        """Return the URL slug used for this language."""
        # Keep default-language home at root if language_slug is intentionally blank.
        if self.is_homepage and self.language == settings.LANGUAGE_CODE and not self.language_slug:
            return ""
        return self.language_slug or self.language
