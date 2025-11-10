"""
Vista para servir robots.txt
"""
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    """Vista para servir robots.txt"""
    robots_content = """# robots.txt para ZenMindConnect 2.0
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /static/
Disallow: /media/
Disallow: /api/

# Sitemap
Sitemap: https://zenmindconnect.com/sitemap.xml
"""
    return HttpResponse(robots_content, content_type='text/plain')

