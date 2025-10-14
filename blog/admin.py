from django.contrib import admin

# Register your models here.
# from modeltranslation.admin import TranslationAdmin
from blog.models import Category, Post
from modeltranslation.admin import TranslationAdmin

@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    pass

@admin.register(Post)
class PostAdmin(TranslationAdmin):
    pass

