from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

from blog.models import Post
from django_restful_translator.models import Translation


class Command(BaseCommand):
    help = "Normalize existing translated slugs using django.utils.text.slugify"

    def add_arguments(self, parser):
        parser.add_argument(
            "--language",
            type=str,
            default=None,
            help="Restrict normalization to a specific language code"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show the changes that would be made without saving them"
        )

    def handle(self, *args, **options):
        language_filter = options["language"]
        dry_run = options["dry_run"]

        post_content_type = ContentType.objects.get_for_model(Post)
        translations = Translation.objects.filter(
            content_type=post_content_type,
            field_name="slug",
        )

        if language_filter:
            translations = translations.filter(language=language_filter)

        updated_count = 0
        for translation in translations.iterator():
            normalized_value = slugify(translation.field_value or "", allow_unicode=True)

            if not normalized_value:
                continue

            if translation.field_value != normalized_value:
                self.stdout.write(
                    f"{translation.language}: '{translation.field_value}' -> '{normalized_value}'"
                )
                updated_count += 1
                if not dry_run:
                    translation.field_value = normalized_value
                    translation.save(update_fields=["field_value"])

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"Dry run complete. {updated_count} translation(s) would be updated."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Normalization complete. {updated_count} translation(s) updated."
            ))