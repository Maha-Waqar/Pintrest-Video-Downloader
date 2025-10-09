# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.blogs, name="blogs"),
    path("<int:pk>", views.blog_detail, name="blog_detail")
]