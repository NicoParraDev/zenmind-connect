"""
Sitemap para SEO de ZenMindConnect 2.0
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post, Persona


class StaticViewSitemap(Sitemap):
    """Sitemap para páginas estáticas."""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'index',
            'nos',
            'frontpage',
            'log',
            'form_persona',
        ]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    """Sitemap para posts del blog."""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Post.objects.filter(date_added__isnull=False).order_by('-date_added')

    def lastmod(self, obj):
        return obj.date_added

