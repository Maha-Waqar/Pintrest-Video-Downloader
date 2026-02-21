# PinCatch – Pinterest Media Downloader

PinCatch is a Django 5.x web app that lets users grab Pinterest images, GIFs, profile pictures, and pins via clean web pages plus a built-in blog. It ships with SEO helpers, rate limiting, multilingual content, and an admin-backed CMS for custom landing pages.

## Features
- Pinterest download tools: image, GIF, profile picture, and generic pin endpoints.
- CMS-driven pages (`pincatch.Page`) with per-language slugs, rich content, and SEO metadata.
- Blog with sitemaps and social-share tags.
- Internationalization: locale switcher, DeepL-powered translations (optional), RTL support.
- Basic abuse controls: CSRF, rate limiting, and User-Agent filtering on downloader endpoints.
- CKEditor for rich text and Rosetta for translation editing.

## Tech Stack
- Python / Django 5.2
- SQLite by default (swap to Postgres/MySQL as needed)
- Static assets served from `static/` → `staticfiles/`

## Quickstart (local development)
1) **Clone & enter**
```bash
git clone <repo-url> pincatch
cd pincatch
```
2) **Create a virtual env (Python 3.10+ recommended)**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```
3) **Install deps**
```bash
pip install -r requirements.txt
```
4) **Configure environment**  
Create `.env` (or export vars) for production-like runs:
```bash
DJANGO_SECRET_KEY=change-me
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com
DJANGO_ADMIN_URL=admin/
DJANGO_ROSETTA_URL=rosetta/
DEEPL_AUTH_KEY=<your-deepl-key>           # required for DeepL translations
PROXY_POOL=http://host:port,https://...    # optional proxy rotation
PROXY_RETRY_STATUSES=403,429,503
PROXY_MAX_FAILURES=3
PROXY_COOLDOWN_SECONDS=60
RATELIMIT_IP_META_KEY=REMOTE_ADDR
```
Notes:
- `DEBUG` is hard-coded `True` in `pincatch/settings.py`; set `DEBUG=False`, add your domain to `ALLOWED_HOSTS`, and set a real `SECRET_KEY` before deploying.
- SQLite DB lives at `db.sqlite3` by default.

5) **Database setup**
```bash
python manage.py migrate
python manage.py createsuperuser
```
6) **Run the dev server**
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000/ for the home page, `/admin/` for Django admin, `/blog/` for posts, and the downloader pages:
- `/pinterest-image-downloader`
- `/pinterest-gif-downloader`
- `/pinterest-profile-picture-downloader`

## Project layout (high level)
- `pincatch/` – core app (pages, SEO helpers, downloader views, translation utilities).
- `blog/` – blog models, views, and sitemaps.
- `templates/` – HTML for pages/blog/downloader views.
- `static/` → collected into `staticfiles/` for production.
- `media/` – uploaded assets (e.g., CKEditor uploads).

## Translation & localization
- Locale catalogs in `locale/` and `drt_locale/`; edit via `/rosetta/` (staff login required).
- Supported language codes are defined in `pincatch/settings.py` (`LANGUAGES`). RTL rendering is enabled when needed.

## Production checklist
- Set `DEBUG=False`, `SECRET_KEY`, and real `ALLOWED_HOSTS`.
- Provide `DJANGO_CSRF_TRUSTED_ORIGINS` for your domain(s).
- Run `python manage.py collectstatic`.
- Use a production DB (Postgres/MySQL) and a proper ASGI/WSGI server (e.g., gunicorn/uvicorn behind Nginx).
- Secure `DEEPL_AUTH_KEY` and proxy values via environment variables or your secrets manager.

## Common commands
- Run tests: `python manage.py test`
- Generate/compile translations: `python manage.py makemessages -l <lang>` then `python manage.py compilemessages`
- Create pages or blog content: use `/admin/` (superuser required).

## Contributing
Issues and PRs are welcome. Please describe the downloader scenario, OS/browser, and any failing URLs when reporting bugs.
