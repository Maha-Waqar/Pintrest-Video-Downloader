# PinBlog Repository Guide

## Overview
- **Project**: PinBlog
- **Primary Framework**: Django
- **Description**: Pinterest-focused web application featuring blog content with multilingual support.
- **Modules**:
  - **pinit/**: Django project configuration and site-level views/templates.
  - **blog/**: Blog application handling posts, categories, translations, and related views.

## Key Dependencies
- **Django**: Core web framework.
- **django_restful_translator**: Handles translation storage and retrieval.
- **django_prose_editor**: Rich text editing for post bodies.
- **DeepL API Integration**: Used via django_restful_translator for automated translations (see `blog/signals.py`).

Refer to `requirements.txt` for the complete dependency list.

## Important Files
- **manage.py**: Django management script.
- **pinit/settings.py**: Project settings including installed apps and localization configuration.
- **pinit/urls.py**: Root URL configuration.
- **blog/models.py**: Post and Category models with translation helpers.
- **blog/views.py**: View functions for listing and detail pages.
- **blog/signals.py**: Translation management logic triggered on model save.
- **templates/**: Site-wide HTML templates.

## Translation & Localization Tips
1. **Translation Storage**: Localized fields are stored via `django_restful_translator.models.Translation` linked to the base object.
2. **Slug Handling**: `Post.get_translated_slug` normalizes slugs with `slugify(..., allow_unicode=True)` to keep them URL-safe.
3. **Language Switching**: The `translate_url` template tag updates the URL path when language changes.
4. **Normalization**: When implementing new features, ensure slugs remain normalized to avoid `%20` issues and mismatches.

## Testing & Debugging
- Use `python manage.py shell` for quick model inspections.
- Run `python manage.py runserver` to test in development.
- Review `DEBUG_TRANSLATION.md` for translation troubleshooting steps.

## Contribution Notes
- Follow Django best practices for models and templates.
- Keep translation logic consistent between templates, views, and signals.
- Avoid editing auto-generated translation strings directly; use the provided translation workflows.
- When adding new routes, update `blog/urls.py` and corresponding views/templates.

