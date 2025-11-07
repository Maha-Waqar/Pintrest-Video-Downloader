from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from blog.models import Post, Category
from django.http import Http404, JsonResponse
from django.utils import translation
from django.utils.text import slugify
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
from django.conf import settings
from django.core.files.storage import default_storage

def blogs(request):
    posts = Post.objects.all().order_by("-created_on")
    # Prefetch translations for the current language
    posts = posts.prefetch_related('translations')
    paginator = Paginator(posts, 12)  # 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    breadcrumbs = [{'title': 'Home', 'url': 'home'}, {'title': 'Blog', 'url': None}]
    context = {
        "blogs": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "current_language": translation.get_language(),
        "breadcrumbs": breadcrumbs,
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
    breadcrumbs = [
        {'title': 'Home', 'url': 'home'},
        {'title': 'Blog', 'url': 'blog'},
        {'title': category, 'url': None}
    ]

    context = {
        "category": matching_category,
        "blogs": posts,
        "current_language": language,
        "breadcrumbs": breadcrumbs,
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

    breadcrumbs = [
        {'title': 'Home', 'url': 'home'},
        {'title': 'Blog', 'url': 'blog'},
        {'title': post.get_translated_title(), 'url': None}
    ]

    context = {
        "blog": post,
        "current_language": language,
        "breadcrumbs": breadcrumbs,
    }
    return render(request, "blog/detail.html", context)

@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = os.path.splitext(file.name)[1].lower()
    
    if file_ext not in allowed_extensions:
        return JsonResponse({'error': 'Invalid file type. Only images are allowed.'}, status=400)
    
    max_size = getattr(settings, 'PROSE_ATTACHMENT_ALLOWED_FILE_SIZE', 10) * 1024 * 1024
    if file.size > max_size:
        return JsonResponse({'error': f'File size exceeds {max_size / (1024 * 1024):.0f}MB limit'}, status=400)
    
    upload_dir = 'prose_uploads/'
    file_path = default_storage.save(
        os.path.join(upload_dir, file.name),
        file
    )
    
    file_url = default_storage.url(file_path)
    
    return JsonResponse({'url': file_url})