# pincatch/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("download", views.download_pinterest_video, name="downloadPinterestVideo"),
    path("downloadVideo", views.download_video, name="downloadVideo"),
    path("downloadImage", views.download_image, name="downloadImage"),
    path("downloadPinterestImage", views.download_pinterest_image, name="downloadPinterestImage"),
    path("downloadGif", views.download_gif, name="downloadGif"),
    path("downloadPinterestGif", views.download_pinterest_gif, name="downloadPinterestGif"),
]
