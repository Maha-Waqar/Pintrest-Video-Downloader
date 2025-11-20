from django.db import migrations, models


def flag_existing_home_pages(apps, schema_editor):
    Page = apps.get_model("pincatch", "Page")
    Page.objects.filter(slug_url="home").update(is_homepage=True)


class Migration(migrations.Migration):

    dependencies = [
        ("pincatch", "0009_rename_pinit_tables"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="is_homepage",
            field=models.BooleanField(
                default=False,
                help_text="If enabled, this page will render at the root URL for the selected language.",
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="slug_url",
            field=models.CharField(
                blank=True,
                help_text="Path component without language, e.g., 'url-downloader'. Leave empty for homepage.",
                max_length=255,
            ),
        ),
        migrations.RunPython(flag_existing_home_pages, migrations.RunPython.noop),
    ]
