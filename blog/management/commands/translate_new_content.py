from django.core.management.base import BaseCommand
from blog.models import Post, Category
from blog.signals import translate_model_instance, translate_with_provider


class Command(BaseCommand):
    help = 'Manually trigger translation for existing models without translations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['post', 'category', 'all'],
            default='all',
            help='Model to translate: post, category, or all'
        )
        parser.add_argument(
            '--provider',
            type=str,
            default='deepl',
            help='Translation provider to use (default: deepl)'
        )

    def handle(self, *args, **options):
        model_choice = options['model']
        provider = options['provider']
        
        if model_choice in ['post', 'all']:
            self.stdout.write('Translating Posts...')
            posts = Post.objects.all()
            for post in posts:
                try:
                    translate_model_instance(post, Post)
                    translate_with_provider(post, Post, provider_name=provider)
                    self.stdout.write(f"✓ Translated: {post.title}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Error translating {post.title}: {e}"))
        
        if model_choice in ['category', 'all']:
            self.stdout.write('Translating Categories...')
            categories = Category.objects.all()
            for category in categories:
                try:
                    translate_model_instance(category, Category)
                    translate_with_provider(category, Category, provider_name=provider)
                    self.stdout.write(f"✓ Translated: {category.name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Error translating {category.name}: {e}"))
        
        self.stdout.write(self.style.SUCCESS('Translation complete!'))