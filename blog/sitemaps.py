from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

from .models import Post, Category


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        names = [
            "home",
            "imageDownloader",
            "gifDownloader",
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
            return reverse("blog_category", args=[category.name.lower()])

    def lastmod(self, item):
        _, category = item
        return category.last_modified


class PinToolSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0
    protocol = "https"

    def items(self):
        return [
            "downloadPinterestVideo",
            "downloadVideo",
            "downloadImage",
            "downloadPinterestImage",
            "downloadGif",
            "downloadPinterestGif",
        ]

    def location(self, item):
        return reverse(item)
