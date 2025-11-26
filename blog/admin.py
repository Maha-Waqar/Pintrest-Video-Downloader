from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from blog.models import Category, Post
from pincatch.models import Page
from blog import translations
from pincatch import translations as page_translations
from django_restful_translator.admin import TranslationInline
from django.contrib.auth.models import User, Group


# Unregister the User model
admin.site.unregister(User)

# Unregister the Group model
admin.site.unregister(Group)

class BaseTranslationAdmin(admin.ModelAdmin):
    readonly_fields = ("created_on", "last_modified")
    inlines = (TranslationInline,)

    def get_list_display(self, request):
        base_fields = super().get_list_display(request)
        merged = []
        seen = set()
        for field in base_fields + ("translate_action",):
            if field not in seen:
                seen.add(field)
                merged.append(field)
        return tuple(merged)


@admin.register(Category)
class CategoryAdmin(BaseTranslationAdmin):
    list_display = ("name", "translate_action", "created_on", "last_modified")

    actions = ["translate_categories"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:category_id>/translate/",
                self.admin_site.admin_view(self.translate_view),
                name="blog_category_translate",
            )
        ]
        return custom_urls + urls

    def translate_view(self, request, category_id):
        redirect_url = self._get_redirect_target(request)
        category = self.get_object(request, category_id)
        if category is None:
            self.message_user(request, _("Category not found."), level=messages.ERROR)
            return HttpResponseRedirect(redirect_url)
        try:
            translations.trigger_category_translation(category.pk, reset_existing=True)
            self.message_user(
                request,
                _("Successfully triggered translation for %(name)s.") % {"name": category.name},
                level=messages.SUCCESS,
            )
        except Exception as exc:  # pragma: no cover - admin feedback only
            self.message_user(
                request,
                _("Failed to translate %(name)s: %(error)s") % {"name": category.name, "error": exc},
                level=messages.ERROR,
            )
        return HttpResponseRedirect(redirect_url)

    def _get_redirect_target(self, request):  # pragma: no cover - simple helper
        return request.META.get("HTTP_REFERER") or reverse("admin:blog_category_changelist")

    def translate_categories(self, request, queryset):
        """Bulk translate selected categories."""
        count = 0
        for category in queryset:
            try:
                translations.trigger_category_translation(category.pk, reset_existing=False)
                count += 1
            except Exception as exc:  # pragma: no cover - admin feedback only
                self.message_user(
                    request,
                    _("Failed to translate %(name)s: %(error)s") % {"name": category.name, "error": exc},
                    level=messages.ERROR,
                )
        if count:
            self.message_user(
                request,
                _("Successfully queued translation for %(count)d categories.") % {"count": count},
                level=messages.SUCCESS,
            )
    translate_categories.short_description = _("Translate selected categories")

    def translate_action(self, obj):
        url = reverse("admin:blog_category_translate", args=[obj.pk])
        return format_html(
            '<a class="button" style="background:#0d6efd;color:#fff;border-color:#0a58ca;padding:6px 12px;border-radius:4px;" href="{}">{}</a>',
            url,
            _("Translate"),
        )

    translate_action.short_description = _("Translate")


@admin.register(Post)
class PostAdmin(BaseTranslationAdmin):
    list_display = ("title", "translate_action", "created_on", "last_modified")

    actions = ["translate_posts"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:post_id>/translate/",
                self.admin_site.admin_view(self.translate_view),
                name="blog_post_translate",
            )
        ]
        return custom_urls + urls

    def translate_view(self, request, post_id):
        redirect_url = self._get_redirect_target(request)
        post = self.get_object(request, post_id)
        if post is None:
            self.message_user(request, _("Post not found."), level=messages.ERROR)
            return HttpResponseRedirect(redirect_url)
        try:
            translations.trigger_post_translation(post.pk, reset_existing=True)
            self.message_user(
                request,
                _("Successfully triggered translation for %(title)s.") % {"title": post.title},
                level=messages.SUCCESS,
            )
        except Exception as exc:  # pragma: no cover - admin feedback only
            self.message_user(
                request,
                _("Failed to translate %(title)s: %(error)s") % {"title": post.title, "error": exc},
                level=messages.ERROR,
            )
        return HttpResponseRedirect(redirect_url)

    def _get_redirect_target(self, request):  # pragma: no cover - simple helper
        return request.META.get("HTTP_REFERER") or reverse("admin:blog_post_changelist")

    def translate_posts(self, request, queryset):
        """Bulk translate selected posts."""
        count = 0
        for post in queryset:
            try:
                translations.trigger_post_translation(post.pk, reset_existing=False)
                count += 1
            except Exception as exc:  # pragma: no cover - admin feedback only
                self.message_user(
                    request,
                    _("Failed to translate %(title)s: %(error)s") % {"title": post.title, "error": exc},
                    level=messages.ERROR,
                )
        if count:
            self.message_user(
                request,
                _("Successfully queued translation for %(count)d posts.") % {"count": count},
                level=messages.SUCCESS,
            )
    translate_posts.short_description = _("Translate selected posts")

    def translate_action(self, obj):
        url = reverse("admin:blog_post_translate", args=[obj.pk])
        return format_html(
            '<a class="button" style="background:#0d6efd;color:#fff;border-color:#0a58ca;padding:6px 12px;border-radius:4px;" href="{}">{}</a>',
            url,
            _("Translate"),
        )

    translate_action.short_description = _("Translate")


@admin.register(Page)
class PageAdmin(BaseTranslationAdmin):
    inlines = ()  # Disable translation inline; each Page is its own language row
    list_display = ("name", "translate_action", "language", "language_slug", "slug_url", "is_homepage", "created_on", "last_modified")
    search_fields = ("name", "slug_url", "language_slug", "meta_title", "meta_description", "content")
    list_filter = ("language", "is_homepage")
    prepopulated_fields = {"slug_url": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug_url", "language", "language_slug", "is_homepage")}),
        (_("Meta"), {"fields": ("meta_title", "meta_description", "meta_keywords")}),
        (_("Head"), {"fields": ("head_html",)}),
        (_("Content"), {"fields": ("content",)}),
        (_("Timestamps"), {"fields": ("created_on", "last_modified")}),
    )
    readonly_fields = ("created_on", "last_modified")
    actions = ["translate_pages"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:page_id>/translate/",
                self.admin_site.admin_view(self.translate_view),
                name="pincatch_page_translate",
            )
        ]
        return custom_urls + urls

    def translate_view(self, request, page_id):
        redirect_url = self._get_redirect_target(request)
        page = self.get_object(request, page_id)
        if page is None:
            self.message_user(request, _("Page not found."), level=messages.ERROR)
            return HttpResponseRedirect(redirect_url)
        if page.language != settings.LANGUAGE_CODE:
            self.message_user(
                request,
                _("Translation can only be triggered from the default language (%(lang)s).") % {"lang": settings.LANGUAGE_CODE},
                level=messages.ERROR,
            )
            return HttpResponseRedirect(redirect_url)
        try:
            page_translations.trigger_page_translation(page.pk, reset_existing=True)
            self.message_user(
                request,
                _("Successfully triggered translation for %(name)s.") % {"name": page.name},
                level=messages.SUCCESS,
            )
        except Exception as exc:  # pragma: no cover - admin feedback only
            self.message_user(
                request,
                _("Failed to translate %(name)s: %(error)s") % {"name": page.name, "error": exc},
                level=messages.ERROR,
            )
        return HttpResponseRedirect(redirect_url)

    def translate_pages(self, request, queryset):
        """Bulk translate selected pages (default language only)."""
        count = 0
        for page in queryset:
            if page.language != settings.LANGUAGE_CODE:
                continue
            try:
                page_translations.trigger_page_translation(page.pk, reset_existing=False)
                count += 1
            except Exception as exc:  # pragma: no cover - admin feedback only
                self.message_user(
                    request,
                    _("Failed to translate %(name)s: %(error)s") % {"name": page.name, "error": exc},
                    level=messages.ERROR,
                )
        if count:
            self.message_user(
                request,
                _("Successfully queued translation for %(count)d pages.") % {"count": count},
                level=messages.SUCCESS,
            )
    translate_pages.short_description = _("Translate selected pages")

    def translate_action(self, obj):
        if obj.language != settings.LANGUAGE_CODE:
            return "-"
        url = reverse("admin:pincatch_page_translate", args=[obj.pk])
        return format_html(
            '<a class="button" style="background:#0d6efd;color:#fff;border-color:#0a58ca;padding:6px 12px;border-radius:4px;" href="{}">{}</a>',
            url,
            _("Translate"),
        )

    translate_action.short_description = _("Translate")

    def _get_redirect_target(self, request):  # pragma: no cover - simple helper
        return request.META.get("HTTP_REFERER") or reverse("admin:pincatch_page_changelist")
