from django.db import models
from django_prose_editor.fields import ProseEditorField
# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=30)
    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    body =  ProseEditorField(
                extensions={
                # Core text formatting
                "Bold": True,
                "Italic": True,
                "Strike": True,
                "Underline": True,
                "HardBreak": True,

                # Structure
                "Heading": {
                    "levels": [1, 2, 3]  # Only allow h1, h2, h3
                },
                "BulletList": True,
                "OrderedList": True,
                "ListItem": True, # Used by BulletList and OrderedList
                "Blockquote": True,

                # Advanced extensions
                "Link": {
                    "enableTarget": True,  # Enable "open in new window"
                    "protocols": ["http", "https", "mailto"],  # Limit protocols
                },
                "Table": True,
                "TableRow": True,
                "TableHeader": True,
                "TableCell": True,

                # Editor capabilities
                "History": True,       # Enables undo/redo
                "HTML": True,          # Allows HTML view
                "Typographic": True,   # Enables typographic chars
            },
            sanitize=True  # Strongly recommended for security
        )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField("Category", related_name="posts")
    image = models.ImageField(upload_to="uploads/", null=True, blank=True)
    def __str__(self):
        return self.title