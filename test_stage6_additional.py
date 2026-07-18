import asyncio
from app.services.conversation_service import ConversationService
from app.sessions.session_manager import UserSession

async def run_additional_tests():
    service = ConversationService()
    
    # Mock search_products to return mock bridal collection data since it is not seeded in the DB
    original_search = service.product_service.repository.search_products
    async def mock_search(query_text=None, category_name=None, max_price=None, limit=100):
        if category_name == "Bridal Collection":
            if max_price and max_price <= 50000.0:
                return [{
                    "id": "2",
                    "name": "Ivory Mriyani Bridal Jewellery Set – Bling Bag",
                    "category": "Bridal Collection",
                    "price": 45332.0,
                    "description": "best",
                    "availability": "In Stock",
                    "image_url": "http://example.com/mriyani.png",
                    "website_url": "http://example.com/bridal"
                }]
            else:
                return [{
                    "id": "100",
                    "name": "Imperial Ruby Bridal Jewellery Set",
                    "category": "Bridal Collection",
                    "price": 450000.0,
                    "description": "Exquisite ruby set.",
                    "availability": "In Stock",
                    "image_url": "http://example.com/ruby.png",
                    "website_url": "http://example.com/bridal"
                }]
        return await original_search(query_text, category_name, max_price, limit)
    service.product_service.repository.search_products = mock_search

    sender_phone = "12345"
    sender_name = "Feature Test"

    print("\n==========================================")
    print("TEST A: Spelling Correction and Prefix")
    print("==========================================")
    session = service.session_manager.get_session(sender_phone)
    session.reset_completely()
    reply_spell = await service.handle_message(sender_phone, "neklace", sender_name)
    print(f"User: neklace\nBot:\n{reply_spell}\n")
    assert "Showing results for Necklace." in reply_spell or "Showing results for Necklaces." in reply_spell, "Should show correction prefix"
    assert "Necklace" in reply_spell or "Set" in reply_spell or "Empress" in reply_spell or "Traditional" in reply_spell, "Should return necklace products"

    print("\n==========================================")
    print("TEST B: Wedding query without direct category")
    print("==========================================")
    session = service.session_manager.get_session(sender_phone)
    session.reset_completely()
    reply_wedding = await service.handle_message(sender_phone, "Wedding jewellery under 50000", sender_name)
    print(f"User: Wedding jewellery under 50000\nBot:\n{reply_wedding}\n")
    assert "Ivory Mriyani" in reply_wedding, "Should return bridal/wedding set under 50000"

    print("\n==========================================")
    print("TEST C: Guided shopping flow - Gift")
    print("==========================================")
    session = service.session_manager.get_session(sender_phone)
    session.reset_completely()
    # Start shopping assistance
    reply_shop1 = await service.handle_message(sender_phone, "I need jewellery", sender_name)
    print(f"User: I need jewellery\nBot:\n{reply_shop1}\n")
    assert "Who is it for?" in reply_shop1, "Should ask for occasion"

    # Provide occasion: Gift
    reply_shop2 = await service.handle_message(sender_phone, "Gift", sender_name)
    print(f"User: Gift\nBot:\n{reply_shop2}\n")
    assert "Who is the gift for?" in reply_shop2, "Should ask for recipient"

    # Provide recipient: Wife
    reply_shop3 = await service.handle_message(sender_phone, "For my wife", sender_name)
    print(f"User: For my wife\nBot:\n{reply_shop3}\n")
    assert "Would you like:" in reply_shop3 or "Rings" in reply_shop3, "Should ask for category first"

    # Provide category: Rings
    reply_shop4 = await service.handle_message(sender_phone, "Rings", sender_name)
    print(f"User: Rings\nBot:\n{reply_shop4}\n")
    assert "What's your approximate budget?" in reply_shop4 or "budget" in reply_shop4.lower(), "Should ask for budget next"

    # Provide budget: 30000
    reply_shop5 = await service.handle_message(sender_phone, "30000", sender_name)
    print(f"User: 30000\nBot:\n{reply_shop5}\n")
    assert "Haily Ring" in reply_shop5 or "flora set" in reply_shop5 or "Minimalist Gold Band" in reply_shop5 or "Ring" in reply_shop5, "Should return rings under 30000"

    print("\n==========================================")
    print("TEST D: Guided shopping flow - Wedding")
    print("==========================================")
    session = service.session_manager.get_session(sender_phone)
    session.reset_completely()
    reply_w1 = await service.handle_message(sender_phone, "I don't know what to buy", sender_name)
    print(f"User: I don't know what to buy\nBot:\n{reply_w1}\n")
    assert "Please tell me:" in reply_w1, "Should show guided message"

    reply_w2 = await service.handle_message(sender_phone, "Wedding", sender_name)
    print(f"User: Wedding\nBot:\n{reply_w2}\n")
    assert "What's your approximate budget?" in reply_w2 or "budget" in reply_w2.lower(), "Should ask for budget next since Wedding maps to Bridal Collection"

    reply_w3 = await service.handle_message(sender_phone, "600000", sender_name)
    print(f"User: 600000\nBot:\n{reply_w3}\n")
    assert "Imperial Ruby" in reply_w3 or "Mriyani" in reply_w3, "Should search and display high-end bridal products"

    print("\n==========================================")
    print("TEST E: Surprise Me flow")
    print("==========================================")
    session = service.session_manager.get_session(sender_phone)
    session.reset_completely()
    reply_surprise = await service.handle_message(sender_phone, "Surprise me", sender_name)
    print(f"User: Surprise me\nBot:\n{reply_surprise}\n")
    assert "recommended products" in reply_surprise, "Should return recommended products"

    print("\nAll new feature tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_additional_tests())
