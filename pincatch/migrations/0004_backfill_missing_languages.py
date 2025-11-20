from django.conf import settings
from django.db import migrations


def ensure_pages_for_all_languages(apps, schema_editor):
    Page = apps.get_model('pincatch', 'Page')
    PageGroup = apps.get_model('pincatch', 'PageGroup')

    languages = [lang[0] for lang in settings.LANGUAGES]

    for group in PageGroup.objects.all():
        existing_langs = set(Page.objects.filter(group=group).values_list('language', flat=True))
        missing_langs = [lang for lang in languages if lang not in existing_langs]
        for language in missing_langs:
            Page.objects.create(
                name=f"Page Title ({language})",
                meta_title=f"Meta Title ({language})",
                meta_description=f"Meta Description ({language})",
                content=f"<p>Content for {language}</p>",
                language=language,
                group=group,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('pincatch', '0003_alter_page_language'),
    ]

    operations = [
        migrations.RunPython(ensure_pages_for_all_languages, reverse_code=migrations.RunPython.noop),
    ]
