from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation
from django.utils.text import slugify

from .models import Post, Category
from pincatch.models import Page


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        names = [
            "home",
            "about",
            "contactUs",
            "privacyPolicy",
            "termsAndConditions",
            "copyrightPolicy",
            "blog",
        ]
        return [
            (language_code, name)
            for language_code, _ in settings.LANGUAGES
            for name in names
        ]

    def location(self, item):
        language_code, name = item
        with translation.override(language_code):
            return reverse(name)


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        return [
            (language_code, post)
            for language_code, _ in settings.LANGUAGES
            for post in Post.objects.all()
        ]

    def location(self, item):
        language_code, post = item
        with translation.override(language_code):
            return reverse("blog_detail", args=[post.slug])

    def lastmod(self, item):
        _, post = item
        return post.last_modified


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        return [
            (language_code, category)
            for language_code, _ in settings.LANGUAGES
            for category in Category.objects.all()
        ]

    def location(self, item):
        language_code, category = item
        with translation.override(language_code):
            category_slug = slugify(category.get_translated_name(language_code), allow_unicode=True)
            return reverse("blog_category", args=[category_slug])

    def lastmod(self, item):
        _, category = item
        return category.last_modified


class PageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Page.objects.all()

    def location(self, page: Page):
        # Homepage URLs are handled separately to respect language-root placement.
        if page.is_homepage:
            lang_slug = page.get_language_slug()
            if lang_slug:
                return reverse("home_language", kwargs={"language_slug": lang_slug})
            return reverse("home")

        language_slug = page.get_language_slug()
        slug = page.slug_url
        return reverse("page_view", kwargs={"language_slug": language_slug, "slug": slug})

    def lastmod(self, page: Page):
        return page.last_modified
