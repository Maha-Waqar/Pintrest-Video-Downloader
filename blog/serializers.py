# blog/serializers.py

from blog.models import Category, Post
from django_restful_translator.drf.serializers import TranslatableDBSerializer

class CategorySerializer(TranslatableDBSerializer):
    class Meta:
        model = Category
        fields = '__all__' 

class PostSerializer(TranslatableDBSerializer):
    class Meta:
        model = Post
        fields = '__all__' 