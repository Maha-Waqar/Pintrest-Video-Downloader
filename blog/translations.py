from blog.models import Post, Category
from blog import signals


def trigger_post_translation(post_id, reset_existing=False):
    """Synchronously trigger translation flow for a post from admin actions."""
    signals._do_post_translation(post_id, reset_existing=reset_existing)


def trigger_category_translation(category_id, reset_existing=False):
    """Synchronously trigger translation flow for a category from admin actions."""
    signals._do_category_translation(category_id, reset_existing=reset_existing)