from typing import Optional
from app.config import settings

class URLBuilder:
    """
    Dedicated URL Builder to abstract URL routing schemes from business logic and database.
    """
    @staticmethod
    def get_category_url(category: str) -> str:
        """
        Generates product category URLs.
        Example: https://ssjewellery.com/?category=Rings
        """
        if not category:
            return URLBuilder.get_website_url()

        cat_lower = category.strip().lower()
        # Map singular or various forms to expected category casing
        cat_map = {
            "ring": "Rings",
            "rings": "Rings",
            "necklace": "Necklaces",
            "necklaces": "Necklaces",
            "earring": "Earrings",
            "earrings": "Earrings",
            "bracelet": "Bracelets",
            "bracelets": "Bracelets",
            "bangle": "Bangles",
            "bangles": "Bangles",
            "chain": "Chains",
            "chains": "Chains",
            "pendant": "Pendants",
            "pendants": "Pendants",
            "bridal": "Bridal Collection",
            "bridal collection": "Bridal Collection"
        }
        normalized = cat_map.get(cat_lower, category.strip().title())
        base = settings.WEBSITE_URL.rstrip('/')
        return f"{base}/?category={normalized}"

    @staticmethod
    def get_website_url() -> str:
        """
        Generates website home page URL.
        Example: https://ssjewellery.com/
        """
        base = settings.WEBSITE_URL.rstrip('/')
        return f"{base}/"

    @staticmethod
    def get_order_url(order_id: Optional[str] = None) -> str:
        """
        Generates order tracking/details URL.
        Returns the website home page as required.
        """
        return URLBuilder.get_website_url()

    @staticmethod
    def get_support_url() -> str:
        """
        Generates support URL.
        """
        base = settings.WEBSITE_URL.rstrip('/')
        return f"{base}/support"
