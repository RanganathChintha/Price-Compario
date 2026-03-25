from flask import Blueprint, render_template, jsonify, request, current_app
from app.services.grok_api import grok_service
from app.services.product_matcher import product_matcher
from app.utils.helpers import ResponseFormatter
from app.utils.logger import logger
import traceback

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Price Compario API is running',
        'services': {
            'grok_api': 'configured' if current_app.config.get('GROK_API_KEY') else 'not configured',
            'cache': 'active'
        }
    })


@main_bp.route('/api/search', methods=['GET'])
def search_products():
    """Search products endpoint"""
    try:
        # Get search query
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(ResponseFormatter.error(
                'Search query is required',
                400
            )), 400
        
        logger.info(f"Searching for: {query}")
        
        # Get filters
        filters = {
            'min_price': request.args.get('min_price', type=float),
            'max_price': request.args.get('max_price', type=float),
            'min_rating': request.args.get('min_rating', type=float),
            'vendor': request.args.get('vendor'),
            'limit': request.args.get('limit', 50, type=int)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Fetch products from Grok API
        products = grok_service.search_products(query, filters)
        
        if not products:
            return jsonify(ResponseFormatter.success({
                'products': [],
                'total_count': 0,
                'message': 'No products found'
            })), 200
        
        # Apply additional filters (if not already applied by API)
        if filters.get('min_price'):
            products = [p for p in products if p['price'] >= filters['min_price']]
        if filters.get('max_price'):
            products = [p for p in products if p['price'] <= filters['max_price']]
        if filters.get('min_rating'):
            products = [p for p in products if p['rating'] >= filters['min_rating']]
        if filters.get('vendor'):
            products = [p for p in products if p['vendor'].lower() == filters['vendor'].lower()]
        
        # Match similar products
        matched_groups = product_matcher.match_products(products)
        
        # Find best overall deal
        all_products = [p for group in matched_groups for p in group['products']]
        best_deal = product_matcher.find_best_overall(all_products) if all_products else None
        
        # Get price statistics
        price_stats = product_matcher.get_price_statistics(all_products)
        
        # Prepare response
        response_data = {
            'products': products,
            'matched_groups': matched_groups,
            'best_deal': best_deal,
            'total_count': len(products),
            'filters_applied': filters,
            'statistics': {
                'price_stats': price_stats,
                'vendor_count': len(set(p['vendor'] for p in products)),
                'average_rating': sum(p['rating'] for p in products) / len(products) if products else 0
            }
        }
        
        logger.info(f"Found {len(products)} products for query: {query}")
        
        return jsonify(ResponseFormatter.success(
            response_data,
            f"Found {len(products)} products"
        )), 200
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}\n{traceback.format_exc()}")
        return jsonify(ResponseFormatter.error(
            'Internal server error',
            500,
            str(e) if current_app.debug else None
        )), 500


@main_bp.route('/api/compare', methods=['POST'])
def compare_products():
    """Compare selected products"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(ResponseFormatter.error('No data provided', 400)), 400
        
        product_ids = data.get('product_ids', [])
        products_data = data.get('products', [])
        
        if not product_ids and not products_data:
            return jsonify(ResponseFormatter.error(
                'No products selected for comparison',
                400
            )), 400
        
        # If products data is provided, use it
        if products_data:
            products = products_data
        else:
            # In production, you'd fetch from cache/database
            # For now, return empty comparison
            products = []
        
        # Group by vendor for comparison view
        comparison_data = {
            'products': products,
            'total_selected': len(products),
            'comparison_table': {
                'headers': ['Feature'] + [p['vendor'] for p in products],
                'rows': []
            }
        }
        
        # Build comparison table if we have products
        if products:
            features = ['Price', 'Rating', 'Availability', 'Shipping', 'Warranty', 'Color']
            rows = []
            
            for feature in features:
                row = {'feature': feature}
                for product in products:
                    if feature == 'Price':
                        row[product['vendor']] = f"${product['price']:.2f}"
                    elif feature == 'Rating':
                        row[product['vendor']] = f"{product['rating']} ★ ({product['rating_count']})"
                    elif feature == 'Availability':
                        row[product['vendor']] = product['availability']
                    elif feature == 'Shipping':
                        row[product['vendor']] = f"${product.get('shipping_cost', 0):.2f}" if product.get('shipping_cost') else 'Free'
                    elif feature == 'Warranty':
                        row[product['vendor']] = product.get('warranty', 'Standard')
                    elif feature == 'Color':
                        row[product['vendor']] = product.get('color', 'Various')
                rows.append(row)
            
            comparison_data['comparison_table']['rows'] = rows
            
            # Find best in each category
            best_price = min(products, key=lambda x: x['price'])
            best_rating = max(products, key=lambda x: x['rating'])
            
            comparison_data['highlights'] = {
                'best_price': {
                    'vendor': best_price['vendor'],
                    'price': best_price['price']
                },
                'best_rating': {
                    'vendor': best_rating['vendor'],
                    'rating': best_rating['rating']
                }
            }
        
        return jsonify(ResponseFormatter.success(
            comparison_data,
            f"Comparing {len(products)} products"
        )), 200
        
    except Exception as e:
        logger.error(f"Error in compare endpoint: {e}\n{traceback.format_exc()}")
        return jsonify(ResponseFormatter.error(
            'Internal server error',
            500,
            str(e) if current_app.debug else None
        )), 500


@main_bp.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get autocomplete suggestions"""
    try:
        query = request.args.get('q', '').strip().lower()
        if not query or len(query) < 2:
            return jsonify(ResponseFormatter.success({'suggestions': []})), 200
        
        # Popular product suggestions
        popular_products = [
            'iPhone', 'Samsung Galaxy', 'Google Pixel', 'OnePlus',
            'MacBook', 'Dell XPS', 'HP Laptop', 'Lenovo ThinkPad',
            'Sony Headphones', 'Bose Headphones', 'AirPods',
            'Apple Watch', 'Samsung Watch', 'Fitbit',
            'iPad', 'Samsung Tablet', 'Microsoft Surface'
        ]
        
        # Filter suggestions based on query
        suggestions = [
            product for product in popular_products
            if query in product.lower()
        ][:10]  # Limit to 10 suggestions
        
        # Add some category suggestions
        categories = ['Smartphones', 'Laptops', 'Headphones', 'Smartwatches', 'Tablets']
        category_suggestions = [
            f"{query} {category}" for category in categories
            if query not in category.lower()
        ][:5]
        
        all_suggestions = list(set(suggestions + category_suggestions))[:10]
        
        logger.debug(f"Generated {len(all_suggestions)} suggestions for '{query}'")
        
        return jsonify(ResponseFormatter.success({
            'suggestions': all_suggestions,
            'query': query
        })), 200
        
    except Exception as e:
        logger.error(f"Error in suggestions endpoint: {e}")
        return jsonify(ResponseFormatter.success({'suggestions': []})), 200


@main_bp.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics (for debugging)"""
    try:
        from app.services.cache import product_cache
        stats = product_cache.get_stats()
        return jsonify(ResponseFormatter.success(stats)), 200
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify(ResponseFormatter.error('Unable to get cache stats', 500)), 500