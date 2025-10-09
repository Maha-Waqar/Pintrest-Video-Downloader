from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from blog.models import Post

def blogs(request):
    posts = Post.objects.all().order_by("-created_on")
    paginator = Paginator(posts, 3)  # 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "blogs": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
    }
    return render(request, "blog/index.html", context)

def blog_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    context = {
        "blog": post
    }
    return render(request, "blog/detail.html", context)