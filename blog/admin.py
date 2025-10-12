from django.contrib import admin

# Register your models here.

from blog.models import Category, Post
from parler.admin import TranslatableAdmin
from django_prose_editor.widgets import ProseEditorWidget

class CategoryAdmin(TranslatableAdmin):
    list_display = ("name",)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Post)