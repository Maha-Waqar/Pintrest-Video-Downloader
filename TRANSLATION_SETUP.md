# Automatic Translation Setup Guide

This document explains how automatic translation works in this Django project.

## Overview

When you save a new `Post` or `Category` model, the following happens automatically:

1. **Signal Detection**: Django signals detect that a new model instance was created
2. **Translation Object Creation**: Empty `Translation` objects are created for each translatable field in each configured language
3. **Auto-Translation**: The content is automatically translated using DeepL (or your configured provider)

## Configuration

### 1. **Configured Languages**

In `pincatch/settings.py`, you have:

```python
LANGUAGES = [
    ('en', _('English')),  # Default language (skipped in auto-translation)
    ('bn', _('Bengali')),
    ('fr', _('French')),
]
```

When you save a Post/Category:
- **English** (default): Original content stored in the model
- **Bengali**: Auto-translated
- **French**: Auto-translated

### 2. **Translation Provider**

The system uses **DeepL** by default (set in `signals.py`).

Make sure you have `DEEPL_AUTH_KEY` in your settings:

```python
# pincatch/settings.py
DEEPL_AUTH_KEY = 'your-deepl-key-here'
```

## How to Use

### Option 1: Automatic Translation (Recommended)

Just save a new Post or Category in Django Admin or via your app:

```python
# When you save this...
post = Post(title="My New Blog Post", body="Content here")
post.save()

# These automatically happen:
# 1. Translation objects are created for Bengali and French
# 2. Content is translated to both languages via DeepL
# 3. You can see translations in templates with {{ post.get_translated_title }}
```

### Option 2: Manual Translation Command

If you want to manually trigger translation for existing models:

```bash
# Translate all Posts and Categories
python manage.py translate_new_content --model all

# Translate only Posts
python manage.py translate_new_content --model post

# Translate only Categories
python manage.py translate_new_content --model category

# Use a different provider (if available)
python manage.py translate_new_content --model all --provider google
```

### Option 3: Django Shell

```python
python manage.py shell

from blog.models import Post
from blog.signals import translate_model_instance, translate_with_provider

post = Post.objects.get(pk=1)

# Create translation objects
translate_model_instance(post, Post)

# Translate with provider
translate_with_provider(post, Post, provider_name='deepl')
```

## Displaying Translations in Templates

Use the helper methods added to your models:

```html
<!-- Show translated title for current language -->
<h1>{{ blog.get_translated_title }}</h1>

<!-- Show translated body for current language -->
<div>{{ blog.get_translated_body|safe }}</div>

<!-- Show translated category name -->
<p>{{ category.get_translated_name }}</p>

<!-- Show translation for specific language -->
<p>{{ blog.get_translated_title|language:"fr" }}</p>
```

## Translatable Fields

Define which fields should be translated in your models:

```python
class Post(TranslatableModel):
    title = models.CharField(max_length=255)
    body = ProseEditorField()
    
    translatable_fields = ['title', 'body']  # These fields will be translated
```

## Database Structure

Translations are stored in the `django_restful_translator_translation` table:

| Column | Value |
|--------|-------|
| content_type | Post (app_label.model_name) |
| object_id | 1 (the Post's primary key) |
| language | 'bn' (Bengali) |
| field_name | 'title' |
| field_value | 'আমার নতুন ব্লগ পোস্ট' (Translated text) |

## Troubleshooting

### Translations Not Appearing

1. **Check if Translation objects exist**:
   ```python
   from django_restful_translator.models import Translation
   Translation.objects.filter(object_id=1).values()
   ```

2. **Check current language**:
   ```python
   from django.utils import translation
   print(translation.get_language())  # Should be 'bn' or 'fr', not 'en'
   ```

3. **Make sure translatable_fields is set**:
   ```python
   Post.translatable_fields  # Should be ['title', 'body']
   ```

### Translation Service Errors

If you see "DeepL API error" in console:

1. Verify `DEEPL_AUTH_KEY` is set in settings
2. Check your DeepL API quota
3. Make sure language codes match (settings.LANGUAGES)

### Signals Not Running

If signals aren't running:

1. Check that `blog.apps.BlogConfig` is in `INSTALLED_APPS`
2. Verify `ready()` method exists in `blog/apps.py`
3. Restart Django server

## Advanced: Disable Auto-Translation

If you want to disable automatic translation for some saves:

**In signals.py**, comment out these lines in the signal handlers:

```python
@receiver(post_save, sender=Post)
def translate_post_on_save(sender, instance, created, **kwargs):
    if created:
        translate_model_instance(instance, Post)
        # translate_with_provider(instance, Post, provider_name='deepl')  # Comment this out
```

## Performance Tips

1. **Batch Processing**: The system uses ThreadPoolExecutor with 4 workers by default (configurable in `signals.py`)

2. **Skip Empty Fields**: Fields with no content are not translated

3. **Cache Translations**: Consider caching translated content in production for faster page loads

```python
# Example caching in views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 60)  # Cache for 1 hour
def blog_detail(request, pk):
    # Your view code
    pass
```

## Files Modified

- `blog/signals.py` - NEW: Signal handlers for automatic translation
- `blog/apps.py` - UPDATED: Added `ready()` method
- `blog/models.py` - UPDATED: Added helper methods for templates
- `blog/management/commands/translate_new_content.py` - NEW: Manual translation command

---

Need help? Check the [django-restful-translator documentation](https://github.com/Attilio/django-restful-translator)