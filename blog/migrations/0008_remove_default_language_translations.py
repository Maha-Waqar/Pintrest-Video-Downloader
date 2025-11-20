from django.conf import settings
from django.db import migrations


def remove_default_language_translations(apps, schema_editor):
    Translation = apps.get_model('django_restful_translator', 'Translation')
    default_language = settings.LANGUAGE_CODE
    Translation.objects.filter(language=default_language).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_delete_sitesettings_post_meta_description_and_more'),
    ]

    operations = [
        migrations.RunPython(remove_default_language_translations, migrations.RunPython.noop),
    ]
