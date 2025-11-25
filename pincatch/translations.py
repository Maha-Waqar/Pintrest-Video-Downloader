import logging
import threading

from django.conf import settings
from django.db import transaction

from pincatch import signals
from pincatch.models import Page

logger = logging.getLogger(__name__)


def _run_in_background(fn, *args, **kwargs):
    """Fire-and-forget wrapper so admin actions don't block the request."""
    def _target():
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.exception("Background page translation failed")
    threading.Thread(target=_target, daemon=True).start()


def _translate_page(page_id, reset_existing):
    try:
        page = Page.objects.get(pk=page_id)
        if page.language != settings.LANGUAGE_CODE:
            logger.info("Skipping translation for non-default language page %s", page_id)
            return
        # force_override mirrors reset_existing behavior: overwrite if True, fill if False
        signals._translate_page_to_other_languages(page, force_override=reset_existing)
    except Exception:
        logger.exception("Failed translating page %s", page_id)


def trigger_page_translation(page_id, reset_existing=False):
    """Trigger translation flow for a Page from admin actions without blocking."""
    transaction.on_commit(
        lambda: _run_in_background(_translate_page, page_id, reset_existing)
    )
