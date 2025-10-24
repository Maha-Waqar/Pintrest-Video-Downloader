"""Refresh translated post bodies so they use localized slugs and cleaned markup."""

from __future__ import annotations

from typing import Iterable, Optional

from django.conf import settings
from django.core.management.base import BaseCommand

from blog.models import Post
from blog.translation_cleanup import build_slug_lookup, clean_translation_html


class Command(BaseCommand):
    """Normalize translated post bodies and ensure localized slugs exist."""

    help = (
        "Re-clean translated post bodies using the latest cleanup rules, ensuring that "
        "internal links target localized slugs and that list/paragraph structure matches the source."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--language",
            help="Restrict normalization to a single language code.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without saving them.",
        )
        parser.add_argument(
            "--post-ids",
            nargs="+",
            type=int,
            help="Optional list of Post IDs to process (defaults to all posts).",
        )

    def handle(self, *args, **options) -> None:
        target_language: Optional[str] = options.get("language")
        dry_run: bool = options.get("dry_run", False)
        post_ids: Optional[Iterable[int]] = options.get("post_ids")

        default_language = settings.LANGUAGE_CODE
        available_languages = [lang[0] for lang in settings.LANGUAGES]

        if target_language:
            if target_language not in available_languages:
                self.stdout.write(
                    self.style.ERROR(f"Language '{target_language}' is not configured.")
                )
                return
            languages = [target_language]
        else:
            languages = [lang for lang in available_languages if lang != default_language]

        queryset = Post.objects.all().prefetch_related("translations")
        if post_ids:
            queryset = queryset.filter(pk__in=post_ids)

        if not queryset.exists():
            self.stdout.write(self.style.WARNING("No posts found for the given criteria."))
            return

        total_updates = 0
        for language in languages:
            slug_lookup = build_slug_lookup(queryset, language)
            updates_for_language = 0

            for post in queryset:
                translation_obj = post.translations.filter(
                    field_name="body",
                    language=language,
                ).first()

                if not translation_obj or not translation_obj.field_value:
                    continue

                cleaned_html = clean_translation_html(
                    post.body,
                    translation_obj.field_value,
                    slug_lookup,
                )

                # Skip if nothing changes (ignoring leading/trailing whitespace).
                if cleaned_html.strip() == (translation_obj.field_value or "").strip():
                    continue

                updates_for_language += 1
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Post {post.pk} ({language}) body would be normalized."
                    )
                else:
                    translation_obj.field_value = cleaned_html
                    translation_obj.save(update_fields=["field_value"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Post {post.pk} ({language}) body normalized and link(s) updated."
                        )
                    )

            total_updates += updates_for_language
            summary_message = (
                f"{updates_for_language} translation(s) updated for language '{language}'."
            )
            if updates_for_language:
                self.stdout.write(self.style.SUCCESS(summary_message))
            else:
                self.stdout.write(summary_message)

        if dry_run:
            self.stdout.write("Dry run complete. No changes were saved.")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Re-clean completed. {total_updates} translation(s) updated in total."
                )
            )