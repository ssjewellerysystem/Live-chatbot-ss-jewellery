import json
import re
from typing import List, Dict, Any, Optional
from app.database.connection import DatabaseConnectionManager
from app.config import settings
from app.exceptions import DatabaseConnectionError

class ProductRepository:
    """
    Repository for Product data access.
    Operates strictly in READ-ONLY mode.
    """

    async def search_products(
        self, 
        query_text: Optional[str] = None, 
        category_name: Optional[str] = None, 
        max_price: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Queries active products matching query_text and/or category_name.
        Filters by category and limits results inside the SQL query.
        Raises DatabaseConnectionError if the database is unreachable or query fails.
        """
        conditions = ["p.status = 'active'"]
        params = []

        if max_price is not None:
            params.append(max_price)
            conditions.append(f"p.price <= ${len(params)}")

        if category_name:
            # Normalize to the exact DB category name (pluralized)
            cat_clean = category_name.strip()
            lower_cat = cat_clean.lower()
            if lower_cat in ["ring", "earring", "necklace", "bracelet", "bangle", "chain", "pendant"]:
                cat_clean = cat_clean + "s"
            elif lower_cat == "bridal":
                cat_clean = "Bridal Collection"
            
            params.append(cat_clean)
            conditions.append(f"c.name ILIKE ${len(params)}")

        if query_text:
            # Clean and split the query into keywords
            clean_query = query_text.lower()
            # Remove price pattern to avoid searching for numbers like 20000 in descriptions
            clean_query = re.sub(r'(?:under|below|less than|max|maximum)\s*(?:rs\.?|inr|₹)?\s*[\d,]+', '', clean_query)
            
            # Replace punctuation with space to isolate words from commas, dots, etc.
            clean_query = re.sub(r'[^\w\s]', ' ', clean_query)
            words = clean_query.split()
            # Comprehensive filler and category keywords to filter out
            exclude_words = {
                "show", "me", "find", "the", "a", "an", "under", "below", "less", "than", 
                "max", "maximum", "ring", "rings", "necklace", "necklaces", "earring", "earrings",
                "bracelet", "bracelets", "bangle", "bangles", "chain", "chains", "pendant", "pendants",
                "collection", "jewellery", "jewelry", "some", "any", "want", "buy", "get",
                "with", "for", "please", "here", "are", "is", "of", "to", "in", "on", "at", "by", "from",
                "about", "would", "like", "can", "you", "could", "search", "display", "list", "give",
                "only", "and", "or"
            }
            keywords = [w for w in words if w not in exclude_words]
            
            for kw in keywords:
                if kw in ("wedding", "bridal"):
                    params.append("%wedding%")
                    params.append("%bridal%")
                    conditions.append(
                        f"(p.name ILIKE ${len(params)-1} OR p.description ILIKE ${len(params)-1} OR c.name ILIKE ${len(params)-1} OR p.name ILIKE ${len(params)} OR p.description ILIKE ${len(params)} OR c.name ILIKE ${len(params)})"
                    )
                else:
                    params.append(f"%{kw}%")
                    conditions.append(
                        f"(p.name ILIKE ${len(params)} OR p.description ILIKE ${len(params)} OR c.name ILIKE ${len(params)})"
                    )

        where_clause = " AND ".join(conditions)

        # Parameterized query to fetch fields
        query = f"""
            SELECT 
                p.id, 
                p.name, 
                p.price, 
                p.description, 
                p.images, 
                p.stock, 
                c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {where_clause}
            ORDER BY 
                p.show_on_homepage DESC NULLS LAST,
                (SELECT COALESCE(SUM(oi.quantity), 0) FROM order_items oi WHERE oi.product_id = p.id) DESC,
                p.ratings DESC NULLS LAST,
                p.created_at DESC NULLS LAST,
                p.id ASC
            LIMIT {limit}
        """

        products = []
        try:
            print(f"Generated SQL:\n{query}\nParameters: {params}")
            rows = await DatabaseConnectionManager.fetch(query, *params)
            for row in rows:
                raw_images = row.get("images")
                images_list = []
                if isinstance(raw_images, str):
                    try:
                        images_list = json.loads(raw_images)
                    except Exception:
                        images_list = []
                elif isinstance(raw_images, list):
                    images_list = raw_images

                image_url = images_list[0] if images_list else ""
                availability = "In Stock" if row.get("stock", 0) > 0 else "Out Of Stock"

                products.append({
                    "id": str(row["id"]),
                    "name": row["name"],
                    "category": row["category_name"] or "Uncategorized",
                    "price": float(row["price"]),
                    "description": row["description"] or "",
                    "availability": availability,
                    "image_url": image_url,
                    "website_url": None
                })
        except Exception as e:
            # Raise DatabaseConnectionError as required by Rule 9
            raise DatabaseConnectionError(f"Database query failure: {e}")

        return products

    @staticmethod
    def slugify(text: str) -> str:
        import re
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s-]+', '-', text)
        return text.strip('-')

    async def get_all_categories(self) -> List[str]:
        """
        Retrieves all category names from PostgreSQL.
        Raises DatabaseConnectionError if the database is unreachable or query fails.
        """
        try:
            rows = await DatabaseConnectionManager.fetch("SELECT DISTINCT name FROM categories ORDER BY name")
            return [row["name"] for row in rows]
        except Exception as e:
            raise DatabaseConnectionError(f"Database query failure: {e}")

