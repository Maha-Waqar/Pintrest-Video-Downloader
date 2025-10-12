from django.db import models
from django_prose_editor.fields import ProseEditorField
from parler.models import TranslatableModel, TranslatedFields

class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=30)
    )

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.safe_translation_getter('name', any_language=True) or ""

class Post():
    # translations = TranslatedFields(
    title=models.CharField(max_length=255),
    body=ProseEditorField(
        extensions={
            "Bold": True,
            "Italic": True,
            "Strike": True,
            "Underline": True,
            "HardBreak": True,
            "Heading": {"levels": [1, 2, 3]},
            "BulletList": True,
            "OrderedList": True,
            "ListItem": True,
            "Blockquote": True,
            "Link": {
                "enableTarget": True,
                "protocols": ["http", "https", "mailto"],
            },
            "Table": True,
            "TableRow": True,
            "TableHeader": True,
            "TableCell": True,
            "History": True,
            "HTML": True,
            "Typographic": True,
        },
        sanitize=True
    ),
    categories = models.ManyToManyField("Category", related_name="posts"),
    created_on = models.DateTimeField(auto_now_add=True),
    last_modified = models.DateTimeField(auto_now=True),
    image = models.ImageField(upload_to="uploads/", null=True, blank=True)

    def __str__(self):
        return self.title