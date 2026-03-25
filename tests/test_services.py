import pytest
from app.services.grok_api import grok_service
from app.services.product_matcher import product_matcher
from app.services.cache import product_cache


def test_grok_api_search():
    """Test Grok API search functionality"""
    products = grok_service.search_products("iPhone", {'limit': 5})
    assert products is not None
    assert len(products) <= 5
    if products:
        assert 'name' in products[0]
        assert 'price' in products[0]
        assert 'vendor' in products[0]


def test_product_matcher():
    """Test product matching logic"""
    # Create test products
    products = [
        {'name': 'iPhone 15', 'price': 999, 'vendor': 'Amazon', 'rating': 4.5, 'availability': 'In Stock'},
        {'name': 'iPhone 15 Pro', 'price': 1199, 'vendor': 'Flipkart', 'rating': 4.7, 'availability': 'In Stock'},
        {'name': 'iPhone 15', 'price': 989, 'vendor': 'Walmart', 'rating': 4.4, 'availability': 'In Stock'},
    ]
    
    matched = product_matcher.match_products(products)
    assert matched is not None
    assert len(matched) <= len(products)


def test_cache():
    """Test caching functionality"""
    # Clear cache
    product_cache.clear()
    assert product_cache.get_stats()['size'] == 0
    
    # Set and get
    product_cache.set('test_key', 'test_value')
    assert product_cache.get('test_key') == 'test_value'
    
    # Clear
    product_cache.clear()
    assert product_cache.get('test_key') is None