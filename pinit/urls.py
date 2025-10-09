# pinit/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("download", views.download_pinterest_video, name="downloadPinterestVideo"),
    path("downloadVideo", views.download_video, name="downloadVideo"),
]