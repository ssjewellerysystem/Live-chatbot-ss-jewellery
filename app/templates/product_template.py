from typing import List
from app.schemas import Product

def format_product_clarification(category: str) -> str:
    """
    Format a clarification prompt when a category is requested but the specific type is incomplete.
    """
    # Capitalize category name for presentation
    cat_title = category.capitalize()
    if cat_title.endswith('s'):
        cat_single = cat_title[:-1]
    else:
        cat_single = cat_title
        
    return (
        f"Which type of {cat_single.lower()} are you looking for?\n"
        f"• Gold {cat_single}\n"
        f"• Diamond {cat_single}\n"
        f"• Silver {cat_single}"
    )

def format_products_list(products: List[Product], query: str) -> str:
    """
    Formats the search result into a professional WhatsApp response.
    """
    if not products:
        return "No matching products found."

    response_parts = []
    # Return at most 3 products to keep the WhatsApp message readable
    for product in products[:3]:
        formatted_price = f"₹{product.price:,.0f}" if product.price % 1 == 0 else f"₹{product.price:,.2f}"
        product_str = (
            f"✨ *{product.name}*\n"
            f"• *Category:* {product.category}\n"
            f"• *Price:* {formatted_price}\n"
            f"• *Availability:* {product.availability}\n"
            f"• *Description:* {product.description}"
        )
        # Only show website link if website_url is present (Rule 7)
        if product.website_url:
            product_str += f"\n🔗 _View Product:_ {product.website_url}"
            
        response_parts.append(product_str)

    header = f"✨ *Here are the matching products I found for \"{query}\":*\n\n"
    return header + "\n\n---\n\n".join(response_parts)

def format_no_products_found() -> str:
    """
    Format a customer-friendly message when no products match the query.
    """
    return (
        "Sorry, I couldn't find matching products.\n\n"
        "Available categories are:\n"
        "💍 Rings\n"
        "📿 Necklaces\n"
        "✨ Pendants\n"
        "👂 Earrings\n"
        "🪬 Bracelets\n"
        "⭕ Bangles\n"
        "⛓️ Chains\n\n"
        "Please choose one category."
    )

