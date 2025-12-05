import logging
import threading

from django.db import transaction

from blog.models import Post, Category
from blog import signals

logger = logging.getLogger(__name__)


def _run_in_background(fn, *args, **kwargs):
    """
    Fire-and-forget wrapper so admin actions don't block the request thread.
    Mirrors the async behavior used for dynamic Page translations.
    """
    def _target():
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.exception("Background blog translation failed")
    threading.Thread(target=_target, daemon=True).start()


def _translate_post_async(post_id, reset_existing):
    signals._do_post_translation(post_id, reset_existing=reset_existing)


def _translate_category_async(category_id, reset_existing):
    signals._do_category_translation(category_id, reset_existing=reset_existing)


def trigger_post_translation(post_id, reset_existing=False):
    """Trigger translation flow for a post without blocking the admin request."""
    transaction.on_commit(
        lambda: _run_in_background(_translate_post_async, post_id, reset_existing)
    )


def trigger_category_translation(category_id, reset_existing=False):
    """Trigger translation flow for a category without blocking the admin request."""
    transaction.on_commit(
        lambda: _run_in_background(_translate_category_async, category_id, reset_existing)
    )
