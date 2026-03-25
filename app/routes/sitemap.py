from flask import Blueprint, make_response
from datetime import datetime

sitemap_bp = Blueprint('sitemap', __name__)


@sitemap_bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap.xml for SEO"""
    pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/search', 'priority': '0.9', 'changefreq': 'always'},
        {'loc': '/compare', 'priority': '0.8', 'changefreq': 'weekly'},
    ]
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>https://pricecompario.com{page["loc"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{datetime.now().date().isoformat()}</lastmod>\n'
        sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response