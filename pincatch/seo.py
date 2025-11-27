from django.utils.translation import gettext_lazy as _

DEFAULT_META_TITLE = _("Pinterest Video Downloader - Image, GIFs & Without Watermark")
DEFAULT_META_DESCRIPTION = _(
    "Bulk free online Pinterest video downloader for PC, Mac, iPhone. "
    "Save 4K videos to MP4 without watermark fast and easy. Scanned by Norton™ Safe Web."
)


def build_seo_context(request, title=None, description=None, canonical_url=None):
    """
    Return a dictionary containing common SEO metadata for templates.
    """
    resolved_canonical = canonical_url
    if not resolved_canonical and request is not None:
        resolved_canonical = request.build_absolute_uri()
    base_site_url = None
    if request is not None:
        try:
            base_site_url = request.build_absolute_uri("/")
        except Exception:
            base_site_url = None

    return {
        "meta_title": title or DEFAULT_META_TITLE,
        "meta_description": description or DEFAULT_META_DESCRIPTION,
        "canonical_url": resolved_canonical,
        "base_site_url": base_site_url,
    }
