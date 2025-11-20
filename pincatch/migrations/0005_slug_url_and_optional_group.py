from django.db import migrations, models
import django.db.models.deletion


def populate_slug_from_group(apps, schema_editor):
    Page = apps.get_model('pincatch', 'Page')
    for page in Page.objects.all():
        if not getattr(page, "slug_url", "") and page.group_id:
            page.slug_url = page.group.slug_url
            page.save(update_fields=["slug_url"])


class Migration(migrations.Migration):

    dependencies = [
        ('pincatch', '0004_backfill_missing_languages'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='slug_url',
            field=models.CharField(default='', help_text="Path component without language, e.g., 'url-downloader'", max_length=255),
        ),
        migrations.AlterField(
            model_name='page',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='pincatch.pagegroup'),
        ),
        migrations.RunPython(populate_slug_from_group, reverse_code=migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together={('slug_url', 'language')},
        ),
    ]
