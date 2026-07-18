import re
from typing import List, Optional
from app.schemas import Product
from app.database.repositories.product_repository import ProductRepository
from app.exceptions import DatabaseConnectionError

SYNONYM_MAP = {
    "ring": "Rings",
    "rings": "Rings",
    
    "neck piece": "Necklaces",
    "neckpiece": "Necklaces",
    "neck pieces": "Necklaces",
    "necklace": "Necklaces",
    "necklaces": "Necklaces",
    
    "pendant": "Pendants",
    "pendents": "Pendants",
    "pendent": "Pendants",
    "pendants": "Pendants",
    
    "ear ring": "Earrings",
    "ear rings": "Earrings",
    "earring": "Earrings",
    "earrings": "Earrings",
    
    "bangle": "Bangles",
    "bangles": "Bangles",
    
    "bracelet": "Bracelets",
    "bracelets": "Bracelets",
    "braclet": "Bracelets",
    "braclets": "Bracelets",
    
    "chain": "Chains",
    "chains": "Chains",
    
    "bridal": "Bridal Collection",
    "bridal collection": "Bridal Collection",
    "wedding": "Bridal Collection",
    "wedding collection": "Bridal Collection"
}

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Standard Levenshtein distance calculation.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

class ProductService:
    """
    Service to handle product querying and filtering.
    Delegates SQL operations to the ProductRepository.
    """
    _cached_categories = None

    def __init__(self):
        self.repository = ProductRepository()

    async def get_categories(self) -> List[str]:
        """
        Retrieves all categories from the database (cached in RAM).
        """
        if ProductService._cached_categories is None:
            try:
                ProductService._cached_categories = await self.repository.get_all_categories()
            except Exception:
                # Fallback to standard categories if DB fails
                ProductService._cached_categories = [
                    "Rings", "Necklaces", "Earrings", "Bracelets", "Bangles", 
                    "Bridal Collection", "Chains", "Pendants"
                ]
        return ProductService._cached_categories

    def normalize_category(self, category_name: Optional[str]) -> Optional[str]:
        if not category_name:
            return None
        cat_lower = category_name.strip().lower()
        return SYNONYM_MAP.get(cat_lower, category_name)

    def match_categories(self, text: str, db_categories: List[str]) -> List[str]:
        """
        Fuzzy matches user input against database categories and synonyms.
        Supports multi-word phrase matching, typo tolerance via Levenshtein distance,
        and multiple category extraction in a single message.
        """
        text_lower = text.lower().strip()
        
        # Candidate dictionary mapping lowercase keys to DB categories
        candidates = {k.lower(): v for k, v in SYNONYM_MAP.items()}
        for cat in db_categories:
            candidates[cat.lower()] = cat
            
        matched = []
        
        # Check multi-word keys first to avoid splitting them (e.g., "bridal collection", "neck pieces", "ear rings")
        multi_word_keys = [k for k in candidates.keys() if " " in k]
        multi_word_keys.sort(key=len, reverse=True)
        
        remaining_text = text_lower
        for mw_key in multi_word_keys:
            pattern = r'\b' + re.escape(mw_key) + r'\b'
            if re.search(pattern, remaining_text):
                cat_val = candidates[mw_key]
                if cat_val not in matched:
                    matched.append(cat_val)
                remaining_text = re.sub(pattern, ' ', remaining_text)
                
        # Clean and tokenize remaining text
        cleaned_text = re.sub(r'[^a-z0-9\s]', ' ', remaining_text)
        tokens = [t for t in cleaned_text.split() if t]
        
        for token in tokens:
            if token in candidates:
                cat_val = candidates[token]
                if cat_val not in matched:
                    matched.append(cat_val)
                continue
                
            # Fuzzy match via Levenshtein distance
            best_match = None
            min_dist = 999
            
            for key, cat in candidates.items():
                if " " in key:
                    continue
                    
                dist = levenshtein_distance(token, key)
                
                # Dynamic typo thresholds
                max_allowed = 0
                if len(key) >= 6:
                    max_allowed = 2
                elif len(key) >= 4:
                    max_allowed = 1
                    
                if dist <= max_allowed and dist < min_dist:
                    min_dist = dist
                    best_match = cat
                    
            if best_match:
                if best_match not in matched:
                    matched.append(best_match)
                
        return matched

    def extract_category_from_text(self, text: str) -> Optional[str]:
        # Legacy/backwards compatibility check
        db_cats = ProductService._cached_categories or ["Rings", "Necklaces", "Earrings", "Bracelets", "Bangles", "Bridal Collection", "Chains", "Pendants"]
        matched = self.match_categories(text, db_cats)
        return matched[0] if matched else None

    def find_closest_category(self, query: str, db_categories: List[str]) -> Optional[str]:
        """
        Finds the closest matching category using Levenshtein distance.
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return None
            
        best_match = None
        min_dist = 999
        
        candidates = {k.lower(): v for k, v in SYNONYM_MAP.items()}
        for cat in db_categories:
            candidates[cat.lower()] = cat
            
        for key, cat in candidates.items():
            dist = levenshtein_distance(query_lower, key)
            if dist < min_dist:
                min_dist = dist
                best_match = cat
                
        max_allowed = max(3, len(query_lower) // 2)
        if min_dist <= max_allowed:
            return best_match
        return None

    async def search_products(self, query: str, category: Optional[str] = None, limit: int = 100) -> List[Product]:
        """
        Searches and filters products by delegating query execution to ProductRepository.
        Supports searching multiple categories.
        """
        db_categories = await self.get_categories()
        
        target_categories = []
        if category:
            target_categories = self.match_categories(category, db_categories)
            
        if not target_categories and query:
            target_categories = self.match_categories(query, db_categories)
            
        # Parse price filter
        query_lower = query.lower() if query else ""
        price_limit: Optional[float] = None
        if query_lower:
            price_match = re.search(r'(?:under|below|less than|max|maximum)\s*(?:rs\.?|inr|₹)?\s*([\d,]+)', query_lower)
            if price_match:
                try:
                    price_str = price_match.group(1).replace(',', '')
                    price_limit = float(price_str)
                except ValueError:
                    pass

        results = []
        if target_categories:
            seen_ids = set()
            for cat in target_categories:
                dict_products = await self.repository.search_products(
                    query_text=query, 
                    category_name=cat,
                    max_price=price_limit,
                    limit=limit
                )
                for p_dict in dict_products:
                    if p_dict["id"] not in seen_ids:
                        seen_ids.add(p_dict["id"])
                        results.append(Product(**p_dict))
        else:
            dict_products = await self.repository.search_products(
                query_text=query, 
                category_name=None,
                max_price=price_limit,
                limit=limit
            )
            for p_dict in dict_products:
                results.append(Product(**p_dict))
                
        return results


