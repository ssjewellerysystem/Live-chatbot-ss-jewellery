import re
import logging
from google import genai
from google.genai import types
from google.genai import errors
from app.config import settings
from app.schemas import Product

logger = logging.getLogger(__name__)

class GeminiFormatter:
    """
    Service to format product captions using Gemini structured prompts.
    Provides a high-fidelity local fallback for robustness and testability.
    """
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def format_product_caption(self, product: Product) -> str:
        """
        Asks Gemini to summarize the product description and format the message
        into a premium WhatsApp layout. Falls back to a local formatter on failure.
        """
        # Format category name for consistency
        category = product.category

        # Format price
        try:
            formatted_price = f"{int(product.price):,}" if product.price % 1 == 0 else f"{product.price:,.2f}"
        except Exception:
            formatted_price = str(product.price)

        prompt = (
            f"You are a premium jewellery copywriter for SSJewellery.\n"
            f"Format the following product details into a beautiful, customer-facing WhatsApp message:\n\n"
            f"Product Name: {product.name}\n"
            f"Category: {category}\n"
            f"Price: ₹{formatted_price}\n"
            f"Availability: {product.availability}\n"
            f"Description: {product.description}\n"
            f"Product URL: {product.website_url}\n\n"
            f"Generate a WhatsApp message using the following layout exactly (with newlines):\n\n"
            f"💍 [Product Name]\n"
            f"💰 ₹[Formatted Price]\n"
            f"📂 [Category]\n"
            f"✅ [Availability]\n"
            f"📝 [Elegant short description summarizing the original description in 1-2 sentences. Do NOT use markdown bold/italics inside the description text itself. Keep it simple and premium.]\n"
            f"🔗 View Product\n"
            f"[Product URL]\n\n"
            f"Requirements:\n"
            f"- Output ONLY the formatted message, nothing else.\n"
            f"- Do NOT add any extra text or conversation wrapper.\n"
            f"- Strictly preserve the exact layout and newlines."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=300
                )
            )

            ai_text = response.text
            if not ai_text:
                raise ValueError("Empty response from Gemini")
            
            # Clean text
            cleaned_text = ai_text.strip()
            # Double check formatting template structure
            if "💍" in cleaned_text and "🔗 View Product" in cleaned_text:
                return cleaned_text

            logger.warning("Gemini response did not conform to template. Using local fallback.")
            return self.format_fallback(product, category, formatted_price)

        except Exception as exc:
            logger.error(f"Gemini formatting failed: {exc}. Using local fallback.")
            return self.format_fallback(product, category, formatted_price)

    def format_fallback(self, product: Product, category: str, formatted_price: str) -> str:
        """
        Local fallback to guarantee correct layout when Gemini is unreachable or rate-limited.
        """
        desc = product.description.strip()
        # Grab first 2 sentences
        sentences = re.split(r'(?<=[.!?])\s+', desc)
        short_desc = " ".join(sentences[:2])
        if not short_desc:
            short_desc = desc
        if len(short_desc) > 180:
            short_desc = short_desc[:177].strip() + "..."

        caption = (
            f"💍 {product.name}\n"
            f"💰 ₹{formatted_price}\n"
            f"📂 {category}\n"
            f"✅ {product.availability}\n"
            f"📝 {short_desc}\n"
            f"🔗 View Product\n"
            f"{product.website_url}"
        )
        return caption
