from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from blog.models import Post, Category
from django.http import Http404
from django.utils import translation
from django.utils.text import slugify
from django.db.models import Q

def blogs(request):
    posts = Post.objects.all().order_by("-created_on")
    # Prefetch translations for the current language
    posts = posts.prefetch_related('translations')
    paginator = Paginator(posts, 12)  # 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "blogs": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "current_language": translation.get_language(),
    }
    return render(request, "blog/index.html", context)

def blog_category(request, category):
    language = translation.get_language()

    matching_category = None
    for cate in Category.objects.all():
        if cate.get_translated_name(language) == category:
            matching_category = cate
            break

    if not matching_category:
        raise Http404("Category not found")

    posts = matching_category.posts.prefetch_related('translations').order_by("-created_on")

    context = {
        "category": matching_category,
        "blogs": posts,
        "current_language": language,
    }
    return render(request, "blog/category.html", context)

def blog_detail(request, slug):
    language = translation.get_language()

    normalized_slug = slugify(slug, allow_unicode=True)

    translated_match = Post.objects.filter(
        translations__language=language,
        translations__field_name='slug'
    ).filter(
        Q(translations__field_value=slug) |
        Q(translations__field_value=normalized_slug)
    ).first()

    if translated_match:
        post = translated_match
    else:
        # Fallback to the base slug when no translated slug exists
        post = get_object_or_404(Post, slug=normalized_slug)

    context = {
        "blog": post,
        "current_language": language,
    }
    return render(request, "blog/detail.html", context)