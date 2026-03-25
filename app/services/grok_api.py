import requests
import time
import logging
from typing import Dict, List, Any, Optional
from app.services.cache import product_cache
from app.utils.helpers import validate_price, validate_rating, generate_product_id
from config import Config
import random

logger = logging.getLogger(__name__)


class GrokAPIService:
    """Service to interact with Grok API for product data"""
    
    def __init__(self):
        self.api_key = Config.GROK_API_KEY
        # Note: Replace with actual Grok API endpoint when available
        self.base_url = "https://api.grok.ai/v1"
        self.cache = product_cache
        self.timeout = 10
        self.max_retries = 3
        
        if not self.api_key or self.api_key == 'your_grok_api_key_here':
            logger.warning("Grok API key not configured. Using mock data.")
    
    def search_products(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Search products using Grok API
        
        Args:
            query: Search query string
            filters: Optional filters (min_price, max_price, min_rating, vendor, limit)
        
        Returns:
            List of normalized product dictionaries
        """
        filters = filters or {}
        
        # Generate cache key
        cache_key = f"search_{query}_{str(filters)}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {query}")
            return cached_result
        
        try:
            # Attempt to call real API
            if self.api_key and self.api_key != 'your_grok_api_key_here':
                products = self._call_grok_api(query, filters)
            else:
                # Use mock data for development
                logger.info(f"Using mock data for query: {query}")
                products = self._get_mock_data(query, filters)
            
            # Cache the results
            if products:
                self.cache.set(cache_key, products)
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            # Fallback to mock data on error
            return self._get_mock_data(query, filters)
    
    def _call_grok_api(self, query: str, filters: Dict) -> List[Dict[str, Any]]:
        """Make actual API call to Grok"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "query": query,
            "limit": filters.get('limit', 50)
        }
        
        # Add optional filters
        if filters.get('min_price'):
            payload['min_price'] = filters['min_price']
        if filters.get('max_price'):
            payload['max_price'] = filters['max_price']
        if filters.get('min_rating'):
            payload['min_rating'] = filters['min_rating']
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/search",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._normalize_products(data.get('products', []))
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Grok API error: {response.status_code} - {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    raise
                continue
            except Exception as e:
                logger.error(f"API call error: {e}")
                if attempt == self.max_retries - 1:
                    raise
                continue
        
        return []
    
    def _normalize_products(self, products: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize product data from API response"""
        normalized = []
        
        for product in products:
            # Validate and format price
            price = validate_price(product.get('price', 0))
            if price is None:
                price = 0.0
            
            # Validate rating
            rating = validate_rating(product.get('rating', 0))
            if rating is None:
                rating = 0.0
            
            normalized_product = {
                'id': generate_product_id(
                    product.get('vendor', 'unknown'),
                    product.get('name', '')
                ),
                'name': product.get('name', 'Unknown Product'),
                'price': price,
                'vendor': product.get('vendor', 'Unknown Vendor'),
                'rating': rating,
                'rating_count': int(product.get('rating_count', 0)),
                'availability': product.get('availability', 'In Stock'),
                'buy_link': product.get('buy_link', '#'),
                'image_url': product.get('image_url', ''),
                'description': product.get('description', ''),
                'shipping_cost': float(product.get('shipping_cost', 0)),
                'warranty': product.get('warranty', 'Standard'),
                'color': product.get('color', 'Various')
            }
            normalized.append(normalized_product)
        
        return normalized
    
    def _get_mock_data(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """Generate realistic mock data for development and testing"""
        
        vendors = [
            {'name': 'Amazon', 'rating': 4.5, 'price_multiplier': 1.0},
            {'name': 'Flipkart', 'rating': 4.3, 'price_multiplier': 0.95},
            {'name': 'Walmart', 'rating': 4.2, 'price_multiplier': 0.98},
            {'name': 'Best Buy', 'rating': 4.4, 'price_multiplier': 1.02},
            {'name': 'Target', 'rating': 4.1, 'price_multiplier': 0.97},
            {'name': 'Newegg', 'rating': 4.3, 'price_multiplier': 0.96},
            {'name': 'eBay', 'rating': 4.0, 'price_multiplier': 0.93}
        ]
        
        # Product categories and base prices
        categories = {
            'smartphone': {'base_price': 699, 'products': ['iPhone', 'Samsung Galaxy', 'Google Pixel', 'OnePlus']},
            'laptop': {'base_price': 999, 'products': ['MacBook', 'Dell XPS', 'HP Spectre', 'Lenovo ThinkPad']},
            'headphones': {'base_price': 199, 'products': ['Sony WH-1000XM4', 'Bose QC45', 'AirPods Pro', 'Sennheiser']},
            'smartwatch': {'base_price': 299, 'products': ['Apple Watch', 'Samsung Watch', 'Garmin', 'Fitbit']},
            'tablet': {'base_price': 499, 'products': ['iPad', 'Samsung Tab', 'Microsoft Surface', 'Amazon Fire']}
        }
        
        # Determine product category from query
        category = None
        for cat in categories:
            if cat in query.lower():
                category = cat
                break
        
        if not category:
            category = 'smartphone'  # Default category
        
        cat_data = categories[category]
        products = []
        
        # Generate 3-5 products per vendor (total 15-25 products)
        for vendor in vendors[:5]:  # Use top 5 vendors
            for i, product_name in enumerate(cat_data['products'][:3]):  # 3 products per vendor
                # Generate random price variation
                price_variation = random.uniform(0.8, 1.2)
                price = cat_data['base_price'] * vendor['price_multiplier'] * price_variation
                
                # Apply price filters if present
                if filters:
                    min_price = filters.get('min_price')
                    max_price = filters.get('max_price')
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue
                
                # Generate rating variation
                rating_variation = random.uniform(-0.3, 0.3)
                rating = min(5.0, max(0, vendor['rating'] + rating_variation))
                
                # Apply rating filter if present
                if filters and filters.get('min_rating'):
                    if rating < filters['min_rating']:
                        continue
                
                # Generate availability
                availability = random.choice(['In Stock', 'In Stock', 'In Stock', 'Limited Stock', 'Out of Stock'])
                
                # Apply vendor filter if present
                if filters and filters.get('vendor'):
                    if filters['vendor'].lower() != vendor['name'].lower():
                        continue
                
                product = {
                    'id': f"{vendor['name'].lower()}_{product_name.lower().replace(' ', '_')}_{i}",
                    'name': f"{product_name} {category.title()} - {random.choice(['Pro', 'Max', 'Plus', 'Ultra', ''])}".strip(),
                    'price': round(price, 2),
                    'vendor': vendor['name'],
                    'rating': round(rating, 1),
                    'rating_count': random.randint(50, 5000),
                    'availability': availability,
                    'buy_link': f"https://{vendor['name'].lower()}.com/search?q={query.replace(' ', '+')}",
                    'image_url': f"https://via.placeholder.com/300x200?text={product_name.replace(' ', '+')}",
                    'description': f"High-quality {category} {product_name} from {vendor['name']}. Features include latest technology, premium build quality, and excellent performance.",
                    'shipping_cost': round(random.uniform(0, 15), 2),
                    'warranty': random.choice(['1 Year', '2 Years', '3 Years', 'Manufacturer Warranty']),
                    'color': random.choice(['Black', 'White', 'Silver', 'Space Gray', 'Gold'])
                }
                products.append(product)
        
        # Limit total products
        limit = filters.get('limit', 50) if filters else 50
        return products[:limit]


# Global service instance
grok_service = GrokAPIService()