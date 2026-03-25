from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ProductMatcher:
    """Service to match similar products across vendors"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize product matcher
        
        Args:
            similarity_threshold: Threshold for matching products (0-1)
        """
        self.similarity_threshold = similarity_threshold
        logger.info(f"Product matcher initialized with threshold {similarity_threshold}")
    
    def match_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group similar products together
        
        Args:
            products: List of product dictionaries
        
        Returns:
            List of matched groups with best deals
        """
        if not products:
            return []
        
        matched_groups = []
        used_indices = set()
        
        for i, product in enumerate(products):
            if i in used_indices:
                continue
            
            # Find similar products
            similar_products = [product]
            similar_indices = [i]
            
            for j, other_product in enumerate(products):
                if j != i and j not in used_indices:
                    similarity = self._calculate_similarity(
                        product['name'],
                        other_product['name']
                    )
                    if similarity >= self.similarity_threshold:
                        similar_products.append(other_product)
                        similar_indices.append(j)
            
            # Mark all similar products as used
            used_indices.update(similar_indices)
            
            # Sort by price to find best deal
            similar_products.sort(key=lambda x: x['price'])
            
            # Find best deal based on price and rating
            best_deal = self._find_best_deal(similar_products)
            
            # Calculate price range
            prices = [p['price'] for p in similar_products]
            
            matched_groups.append({
                'products': similar_products,
                'best_deal': best_deal,
                'price_range': {
                    'min': min(prices),
                    'max': max(prices),
                    'difference': max(prices) - min(prices),
                    'savings': (max(prices) - min(prices)) / max(prices) * 100 if max(prices) > 0 else 0
                },
                'product_name': similar_products[0]['name'],
                'vendor_count': len(similar_products)
            })
        
        # Sort groups by price range (best deals first)
        matched_groups.sort(key=lambda x: x['price_range']['min'])
        
        return matched_groups
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names"""
        # Convert to lowercase and remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 'with', 'by'}
        
        def clean_name(name):
            words = name.lower().split()
            words = [w for w in words if w not in common_words]
            return ' '.join(words)
        
        name1_clean = clean_name(name1)
        name2_clean = clean_name(name2)
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, name1_clean, name2_clean).ratio()
        
        # Boost similarity if they share key features
        if self._share_key_features(name1, name2):
            similarity = min(1.0, similarity + 0.1)
        
        return similarity
    
    def _share_key_features(self, name1: str, name2: str) -> bool:
        """Check if products share key features (brand, model, etc.)"""
        # Extract potential model numbers or key identifiers
        import re
        
        # Look for model numbers (e.g., X1000, Pro, Max)
        model_pattern = r'\b([A-Z]+[0-9]+|[A-Z][a-z]+(?:Pro|Max|Plus|Ultra))\b'
        
        models1 = set(re.findall(model_pattern, name1, re.IGNORECASE))
        models2 = set(re.findall(model_pattern, name2, re.IGNORECASE))
        
        return bool(models1 & models2)
    
    def _find_best_deal(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find the best deal based on price and rating
        
        Scoring: 60% price, 40% rating
        """
        if not products:
            return None
        
        # Normalize prices (lower is better)
        max_price = max(p['price'] for p in products)
        
        def calculate_score(product):
            # Price score: lower price = higher score
            price_score = 1 - (product['price'] / max_price) if max_price > 0 else 0
            
            # Rating score: higher rating = higher score
            rating_score = product['rating'] / 5
            
            # Combined score (60% price, 40% rating)
            return (price_score * 0.6) + (rating_score * 0.4)
        
        best_product = max(products, key=calculate_score)
        
        # Add reason for being best deal
        best_product['best_deal_reason'] = self._get_best_deal_reason(
            best_product, products
        )
        
        return best_product
    
    def _get_best_deal_reason(self, best: Dict, all_products: List[Dict]) -> str:
        """Generate reason why this is the best deal"""
        if len(all_products) <= 1:
            return "Only option available"
        
        avg_price = sum(p['price'] for p in all_products) / len(all_products)
        price_diff = avg_price - best['price']
        price_saving_percent = (price_diff / avg_price) * 100 if avg_price > 0 else 0
        
        if price_saving_percent > 20:
            return f"Best price - {price_saving_percent:.0f}% cheaper than average"
        elif best['rating'] > 4.5:
            return f"Highest rated - {best['rating']} stars"
        elif best['rating'] > 4.0 and price_saving_percent > 10:
            return f"Great value - High rating with {price_saving_percent:.0f}% savings"
        elif best['price'] == min(p['price'] for p in all_products):
            return f"Lowest price - ${best['price']:.2f}"
        else:
            return "Best overall value"
    
    def find_best_overall(self, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the single best product from all products"""
        if not products:
            return None
        
        # Calculate score for each product
        max_price = max(p['price'] for p in products)
        
        def calculate_overall_score(product):
            price_score = 1 - (product['price'] / max_price) if max_price > 0 else 0
            rating_score = product['rating'] / 5
            availability_score = 1 if product['availability'] == 'In Stock' else 0.5
            
            # Weighted: 50% price, 30% rating, 20% availability
            return (price_score * 0.5) + (rating_score * 0.3) + (availability_score * 0.2)
        
        best = max(products, key=calculate_overall_score)
        
        # Add metadata
        best['overall_score'] = calculate_overall_score(best)
        best['is_best_overall'] = True
        
        return best
    
    def group_by_vendor(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Group products by vendor"""
        vendor_groups = defaultdict(list)
        for product in products:
            vendor_groups[product['vendor']].append(product)
        return dict(vendor_groups)
    
    def get_price_statistics(self, products: List[Dict[str, Any]]) -> Dict:
        """Get price statistics for products"""
        if not products:
            return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
        
        prices = sorted([p['price'] for p in products])
        n = len(prices)
        
        return {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / n,
            'median': prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2,
            'range': max(prices) - min(prices)
        }


# Global matcher instance
product_matcher = ProductMatcher()