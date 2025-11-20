from django.db import migrations, models
import ckeditor_uploader.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="No Title", max_length=255)),
                ("meta_title", models.CharField(default="Meta Title")),
                ("meta_description", models.TextField(default="Meta Description")),
                ("slug_url", models.CharField(max_length=255, unique=True)),
                ("content", ckeditor_uploader.fields.RichTextUploadingField()),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("last_modified", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
