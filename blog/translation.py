# blog/translation.py
from modeltranslation.translator import translator, TranslationOptions
from blog.models import Category, Post

class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)  # Fields to be translated

class PostTranslationOptions(TranslationOptions):
    fields = ('title', 'body')  # Fields to be translated

translator.register(Category, CategoryTranslationOptions)
translator.register(Post, PostTranslationOptions)
