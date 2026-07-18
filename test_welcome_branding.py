import asyncio
from app.config import settings
from app.services.conversation_service import ConversationService

async def run_welcome_tests():
    # Setup test logo url and caption from settings
    if not settings.WELCOME_LOGO_URL:
        settings.WELCOME_LOGO_URL = "http://localhost:8000/static/logo/logo.png"

    service = ConversationService()
    
    # Mock send_image_message to capture calls
    sent_images = []
    async def mock_send_image_message(recipient_phone, image_url, caption=None):
        sent_images.append((recipient_phone, image_url, caption))
        print(f"--- [Mock API Call] Sent Image to {recipient_phone}: {image_url} (Caption: {caption}) ---")

    service.image_response_builder.whatsapp_client.send_image_message = mock_send_image_message

    sender_phone = "919999999999"
    sender_name = "Welcome Tester"

    print("\n==========================================")
    print("Scenario 1: New User Greeting (Hi)")
    print("==========================================")
    session = service.session_manager.get_session(sender_phone)
    session.reset_completely()
    
    sent_images.clear()
    reply = await service.handle_message(sender_phone, "Hi", sender_name)
    print(f"Reply:\n{reply}\n")
    
    assert reply == "", "Should return empty string to prevent sending a second message"
    assert len(sent_images) == 1, "Should have triggered exactly 1 image message"
    assert sent_images[0][0] == sender_phone, "Incorrect recipient phone"
    assert sent_images[0][1] == settings.WELCOME_LOGO_URL, "Incorrect logo URL"
    assert "💎 Welcome to SSJewellery" in sent_images[0][2], "Missing welcome branding in caption"
    assert "Hello, Sir/Madam! 👋" in sent_images[0][2], "Name should not be personalized, must use Sir/Madam"
    assert "Timeless Elegance, Crafted For You ✨" not in sent_images[0][2], "Old caption must be removed"
    print("Scenario 1 passed!")

    print("\n==========================================")
    print("Scenario 2: Active Conversation Transition to Product Search")
    print("==========================================")
    # User sends "Show me rings" in active session after greeting
    sent_images.clear()
    reply2 = await service.handle_message(sender_phone, "Show me rings", sender_name)
    print(f"Reply:\n{reply2}\n")
    
    assert len(sent_images) == 0, "No welcome image should be sent in an active session"
    assert "Eternity Diamond" in reply2 or "Rings" in reply2 or "Showing results for" in reply2, "Product search should start immediately"
    print("Scenario 2 passed!")

    print("\n==========================================")
    print("Scenario 3: User Session Timeout -> Greeting Again")
    print("==========================================")
    # Modify session last_accessed to trigger expiration
    session = service.session_manager.get_session(sender_phone)
    session.last_accessed = 0.0 # Force timeout
    
    sent_images.clear()
    reply3 = await service.handle_message(sender_phone, "Hi", sender_name)
    print(f"Reply:\n{reply3}\n")
    
    assert reply3 == "", "Should return empty string to prevent second message"
    assert len(sent_images) == 1, "Should send Welcome Image again after session timeout"
    assert "💎 Welcome to SSJewellery" in sent_images[0][2], "Missing welcome branding in caption"
    assert "Hello, Sir/Madam! 👋" in sent_images[0][2], "Must use Sir/Madam"
    print("Scenario 3 passed!")

    print("\n==========================================")
    print("Scenario 4: Direct Transition to another search query")
    print("==========================================")
    # User sends "Show me necklace" without greeting in the active session
    sent_images.clear()
    reply4 = await service.handle_message(sender_phone, "Show me necklace", sender_name)
    print(f"Reply:\n{reply4}\n")
    
    assert len(sent_images) == 0, "No welcome image should be sent"
    assert "Necklace" in reply4 or "Set" in reply4 or "Choker" in reply4 or "Empress" in reply4 or "Showing results for" in reply4, "Should search necklace immediately"
    print("Scenario 4 passed!")

    print("\nAll Welcome Branding Experience Tests Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_welcome_tests())
