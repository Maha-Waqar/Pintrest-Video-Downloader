#!/usr/bin/env python
"""
Quick test script to verify translation signals are working
Run with: python test_signals.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinit.settings')
django.setup()

from blog.models import Post
from django_restful_translator.models import Translation
from django.conf import settings

print("\n" + "="*60)
print("TESTING TRANSLATION SIGNALS")
print("="*60)

# Configuration check
print("\n✓ Configuration:")
print(f"  - Default Language: {settings.LANGUAGE_CODE}")
print(f"  - Target Languages: {[lang[0] for lang in settings.LANGUAGES if lang[0] != settings.LANGUAGE_CODE]}")
print(f"  - DeepL API Key Set: {bool(settings.DEEPL_AUTH_KEY)}")

# Test signal
print("\n⏳ Creating test post...")
test_post = Post.objects.create(
    title="🧪 Signal Test Post",
    body="<p>Testing automatic translation signals</p>"
)
print(f"✓ Post created with ID: {test_post.pk}")

# Check for translations
print("\n⏳ Checking for translations...")
translations = Translation.objects.filter(object_id=test_post.pk)
count = translations.count()

print(f"✓ Found {count} translation objects\n")

if count == 0:
    print("⚠️  WARNING: No translation objects found!")
    print("   This means the signal did not trigger or failed silently.")
    print("\n   Try this:")
    print("   1. Check Django console for any error messages")
    print("   2. Verify blog.apps.BlogConfig is in INSTALLED_APPS")
    print("   3. Run: python manage.py shell")
    print("   4. Then: from blog.models import Post")
    print("   5. Then: post = Post.objects.create(title='test', body='test')")
    print("   6. Check console logs")
else:
    print("Translation Objects Created:")
    print("-" * 60)
    for translation in translations:
        status = "✓ Translated" if translation.field_value else "⏳ Pending"
        preview = translation.field_value[:40] + "..." if translation.field_value else "(empty)"
        print(f"  {status} | {translation.language:3s} | {translation.field_name:10s} | {preview}")
    print("-" * 60)

print("\n" + "="*60)
print("END OF TEST")
print("="*60 + "\n")