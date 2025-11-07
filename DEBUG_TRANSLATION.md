# Translation Debugging Guide

## Step 1: Configure Logging

Add this to your `pinit/settings.py` to see detailed logs:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'blog.signals': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django_restful_translator': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## Step 2: Test the Signal

Run Django in debug mode and watch for logs:

```bash
# Terminal 1: Start Django development server
python manage.py runserver

# Terminal 2: Open Django shell
python manage.py shell

# Then run this:
from blog.models import Post

# Create a new post
post = Post.objects.create(
    title="Test Post",
    body="<p>Test Content</p>"
)

# You should see logs like:
# INFO:blog.signals:Signal received for Post: 1, created=True
# INFO:blog.signals:Post 1 is NEW. Starting translation...
# INFO:blog.signals:translate_model_instance called for Post 1
```

## Step 3: Check if Translation Objects Were Created

```python
from django_restful_translator.models import Translation
from blog.models import Post

post = Post.objects.latest('pk')

# Check all translations for this post
translations = Translation.objects.filter(object_id=post.pk)
for t in translations:
    print(f"{t.language} - {t.field_name}: {t.field_value[:50]}...")

# Should show something like:
# bn - title: আমার নতুন ব্লগ পোস্ট...
# bn - body: <p>পরীক্ষা কন্টেন্ট</p>...
# fr - title: Mon nouveau message de blog...
# fr - body: <p>Contenu de test</p>...
```

## Step 4: Common Issues & Solutions

### Issue 1: Signal Not Firing at All

**Check Console Output:**
- You should see `Signal received for Post:` logs
- If nothing appears, signals aren't registered

**Solution:**
```bash
# Restart Django server completely
python manage.py runserver

# Check apps.py is correct:
# - blog.apps.BlogConfig should be in INSTALLED_APPS
# - ready() method should import blog.signals
```

### Issue 2: Translation Objects Created But Not Translated

**Check Logs:**
- Should see `translate_with_provider called`
- Should see `Submitting translation job`
- If not, the provider call is failing

**Solution:**
```python
# Check if DeepL API key is configured
from django.conf import settings
print(settings.DEEPL_AUTH_KEY)  # Should not be empty

# Test DeepL directly
from django_restful_translator.translation_providers import TranslationProviderFactory
provider = TranslationProviderFactory.get_provider('deepl')
print(provider)  # Should not raise error
```

### Issue 3: Empty Translation Values

**Check Console:**
- Should see `Translation object created successfully`
- But `field_value` is empty in database

**Solution:**
This can mean the translation service didn't complete. Check:

```python
# Check if DeepL API is working
from django.conf import settings
import httpx

headers = {'Authorization': f'DeepL-Auth-Key {settings.DEEPL_AUTH_KEY}'}
response = httpx.post(
    'https://api-free.deepl.com/v2/translate',
    headers=headers,
    data={'text': 'Hello', 'target_lang': 'BN'}
)
print(response.json())  # Should work without errors
```

### Issue 4: Signals Working in Shell But Not Admin

**Reason:** Django Admin might use transactions differently

**Solution:**
```python
# In Django shell (works):
post = Post.objects.create(title="Test", body="Content")

# In Django admin (might not work): 
# Django wraps admin saves in transactions
# Our signal fires but might not see Translation objects if they're
# in a different transaction

# Solution: Update settings.py to disable transaction wrapping for signals
# Or use on_commit() hook:
```

## Step 5: Full Debugging Script

Run this script to test everything:

```python
# save as debug_translation.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinit.settings')
django.setup()

from blog.models import Post, Category
from django_restful_translator.models import Translation
from django_restful_translator.translation_providers import TranslationProviderFactory
from django.conf import settings

print("=" * 60)
print("TRANSLATION DEBUGGING")
print("=" * 60)

# 1. Check Configuration
print("\n1. CONFIGURATION CHECK")
print(f"   Default Language: {settings.LANGUAGE_CODE}")
print(f"   Configured Languages: {[lang[0] for lang in settings.LANGUAGES]}")
print(f"   DeepL Key Set: {bool(settings.DEEPL_AUTH_KEY)}")

# 2. Check Translatable Fields
print("\n2. TRANSLATABLE FIELDS")
print(f"   Post: {Post.translatable_fields}")
print(f"   Category: {Category.translatable_fields}")

# 3. Check Provider
print("\n3. PROVIDER CHECK")
try:
    provider = TranslationProviderFactory.get_provider('deepl')
    print(f"   Provider: {provider}")
    print(f"   Batch Size: {provider.batch_size}")
except Exception as e:
    print(f"   ERROR: {e}")

# 4. Test Signal
print("\n4. TESTING SIGNAL")
print("   Creating test post...")
test_post = Post.objects.create(
    title="Debug Test Post",
    body="<p>Debug test content</p>"
)
print(f"   Post created: {test_post.pk}")

# 5. Check Translation Objects
print("\n5. CHECKING TRANSLATION OBJECTS")
translations = Translation.objects.filter(object_id=test_post.pk)
print(f"   Total translations found: {translations.count()}")
for t in translations:
    value_preview = t.field_value[:50] if t.field_value else "(EMPTY)"
    print(f"   - {t.language} / {t.field_name}: {value_preview}")

# 6. Manual Translation Test
print("\n6. MANUAL TRANSLATION TEST")
from blog.signals import translate_model_instance, translate_with_provider
try:
    translate_with_provider(test_post, Post, provider_name='deepl')
    print("   Manual translation attempted")
    
    # Check again
    translations = Translation.objects.filter(object_id=test_post.pk)
    for t in translations:
        value_preview = t.field_value[:50] if t.field_value else "(EMPTY)"
        print(f"   - {t.language} / {t.field_name}: {value_preview}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)
```

Run it:
```bash
python debug_translation.py
```

## Step 6: Check if Signals Are Imported

```python
python manage.py shell

# Try importing signals directly
try:
    import blog.signals
    print("✓ Signals imported successfully")
except Exception as e:
    print(f"✗ Error importing signals: {e}")

# Check if receivers are registered
from django.db.models import signals
from blog.models import Post

receivers = signals.post_save.receivers_for_signal()
print(f"Receivers for Post save signal: {len(receivers)}")
```

## Step 7: Enable Full Debug Mode

In `pinit/settings.py`, add:

```python
# Add at the end
import logging
logging.basicConfig(level=logging.DEBUG)

# Increase verbosity
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

**After following these steps, paste the output in your response and I can help identify the exact issue!**