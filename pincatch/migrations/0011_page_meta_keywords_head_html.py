from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pincatch", "0010_homepage_support"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="meta_keywords",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="page",
            name="head_html",
            field=models.TextField(blank=True, default=""),
        ),
    ]
