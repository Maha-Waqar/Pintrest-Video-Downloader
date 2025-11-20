from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_pages_to_groups(apps, schema_editor):
    Page = apps.get_model('pincatch', 'Page')
    PageGroup = apps.get_model('pincatch', 'PageGroup')

    default_language = getattr(settings, 'LANGUAGE_CODE', 'en')

    for page in Page.objects.all():
        slug_value = getattr(page, 'slug_url', None) or f'page-{page.pk}'
        group, _ = PageGroup.objects.get_or_create(slug_url=slug_value)
        if not page.language:
            page.language = default_language
        page.group_id = group.id
        page.save(update_fields=['language', 'group'])


class Migration(migrations.Migration):

    dependencies = [
        ('pincatch', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug_url', models.CharField(max_length=255, unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='page',
            name='language',
            field=models.CharField(choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE, max_length=10),
        ),
        migrations.AddField(
            model_name='page',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='pincatch.pagegroup'),
        ),
        migrations.RunPython(migrate_pages_to_groups, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='page',
            name='slug_url',
        ),
        migrations.AlterField(
            model_name='page',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='pincatch.pagegroup'),
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together={('group', 'language')},
        ),
    ]
