# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.blogs, name="blogs"),
    path("<slug>/", views.blog_detail, name="blog_detail"),
    path("category/<category>/", views.blog_category, name="blog_category"),
]