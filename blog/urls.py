# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.blogs, name="blog"),
    path("<slug>/", views.blog_detail, name="blog_detail"),
    path("category/<slug:category_slug>/", views.blog_category, name="blog_category"),
]
