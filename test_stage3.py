import asyncio
import time
from app.services.conversation_service import ConversationService
from app.demo.orders import DEMO_ORDERS
from app.demo.tickets import DEMO_TICKETS

async def run_tests():
    print("Initializing Conversation Service...")
    service = ConversationService()
    
    # Mock send_image_message to capture calls
    sent_images = []
    async def mock_send_image_message(recipient_phone, image_url, caption=None):
        sent_images.append((recipient_phone, image_url, caption))
        print(f"--- [Mock API Call] Sent Image to {recipient_phone}: {image_url} (Caption: {caption}) ---")

    service.image_response_builder.whatsapp_client.send_image_message = mock_send_image_message
    
    sender_phone = "919999999999"
    sender_name = "Alice Test"

    print("\n==========================================")
    print("TEST 1: Greeting Conversation")
    print("==========================================")
    sent_images.clear()
    reply1 = await service.handle_message(sender_phone, "Hi", sender_name)
    print(f"User: Hi")
    print(f"Bot:\n{reply1}\n")
    assert reply1 == "", "Should return empty string to prevent sending a second message"
    assert len(sent_images) == 1, "Should send exactly one welcome image"
    assert "💎 Welcome to SSJewellery" in sent_images[0][2]
    assert "Hello, Sir/Madam! 👋" in sent_images[0][2]

    print("\n==========================================")
    print("TEST 2: Support Ticket Step-by-Step Flow")
    print("==========================================")
    reply_sup1 = await service.handle_message(sender_phone, "Need support", sender_name)
    print(f"User: Need support")
    print(f"Bot:\n{reply_sup1}\n")
    assert "Please briefly describe your issue." in reply_sup1

    reply_sup2 = await service.handle_message(sender_phone, "My ring size is incorrect.", sender_name)
    print(f"User: My ring size is incorrect.")
    print(f"Bot:\n{reply_sup2}\n")
    assert "Please enter your email address." in reply_sup2

    reply_sup3 = await service.handle_message(sender_phone, "invalid-email-format", sender_name)
    print(f"User: invalid-email-format")
    print(f"Bot:\n{reply_sup3}\n")
    assert "doesn't look quite right" in reply_sup3

    reply_sup4 = await service.handle_message(sender_phone, "alice@example.com", sender_name)
    print(f"User: alice@example.com")
    print(f"Bot:\n{reply_sup4}\n")
    assert "Support Ticket Created" in reply_sup4
    assert "My ring size is incorrect" in reply_sup4
    assert "alice@example.com" in reply_sup4

    print("\n==========================================")
    print("TEST 3: Order Tracking Step-by-Step Flow")
    print("==========================================")
    reply_ord1 = await service.handle_message(sender_phone, "Track my order", sender_name)
    print(f"User: Track my order")
    print(f"Bot:\n{reply_ord1}\n")
    assert "Please enter your Order ID." in reply_ord1

    # Using SJ10245 from the expanded demo dataset
    reply_ord2 = await service.handle_message(sender_phone, "SJ10245", sender_name)
    print(f"User: SJ10245")
    print(f"Bot:\n{reply_ord2}\n")
    assert "Order Status Details" in reply_ord2
    assert "SJ10245" in reply_ord2

    print("\n==========================================")
    print("TEST 4: Generic Product Search Flow")
    print("==========================================")
    reply_prod1 = await service.handle_message(sender_phone, "Show me jewellery", sender_name)
    print(f"User: Show me jewellery")
    print(f"Bot:\n{reply_prod1}\n")
    assert "Which category are you looking for?" in reply_prod1

    reply_prod2 = await service.handle_message(sender_phone, "Rings", sender_name)
    print(f"User: Rings")
    print(f"Bot:\n{reply_prod2}\n")
    assert "Classic Solitaire Diamond Ring" in reply_prod2 or "Eternity Diamond Band" in reply_prod2 or "Royal Emerald Cascade" in reply_prod2


    print("\n==========================================")
    print("TEST 5: Direct Intent Handling (Skipping Flows)")
    print("==========================================")
    # Direct order tracking with Order ID in the text
    reply_direct_ord = await service.handle_message(sender_phone, "Track my order SJ10241", sender_name)
    print(f"User: Track my order SJ10241")
    print(f"Bot:\n{reply_direct_ord}\n")
    assert "Order Status Details" in reply_direct_ord
    assert "SJ10241" in reply_direct_ord

    # Direct product search
    reply_direct_prod = await service.handle_message(sender_phone, "Show me diamond necklaces", sender_name)
    print(f"User: Show me diamond necklaces")
    print(f"Bot:\n{reply_direct_prod}\n")
    assert "Regal Emerald & Pearl Necklace" in reply_direct_prod or "Queen Emerald" in reply_direct_prod or "Imperial Diamond Choker" in reply_direct_prod

    print("\n==========================================")
    print("TEST 6: Context Switching Mid-Flow")
    print("==========================================")
    service.session_manager.get_session(sender_phone).reset_completely()
    # Start support ticket
    reply_switch1 = await service.handle_message(sender_phone, "Need support", sender_name)
    print(f"User: Need support")
    print(f"Bot:\n{reply_switch1}\n")
    
    # Send order tracking to switch context
    reply_switch2 = await service.handle_message(sender_phone, "Track order", sender_name)
    print(f"User: Track order")
    print(f"Bot:\n{reply_switch2}\n")
    assert "Please enter your Order ID." in reply_switch2, "Should switch to order tracking"

    print("\n==========================================")
    print("TEST 7: Session Expiration Timeout")
    print("==========================================")
    # Start order tracking
    reply_time1 = await service.handle_message(sender_phone, "Track my order", sender_name)
    print(f"User: Track my order")
    print(f"Bot:\n{reply_time1}\n")
    
    # Mock expiration by modifying session access time
    session = service.session_manager.get_session(sender_phone)
    session.last_accessed = time.time() - 301.0 # 5 minutes + 1 second ago
    
    # Next message should reset and trigger greeting because we timeout and get greeting
    sent_images.clear()
    reply_time2 = await service.handle_message(sender_phone, "Hi", sender_name)
    print(f"User: Hi (after timeout)")
    print(f"Bot:\n{reply_time2}\n")
    assert reply_time2 == "", "Should return empty string to prevent sending a second message"
    assert len(sent_images) == 1, "Should send exactly one welcome image on timeout"
    assert "💎 Welcome to SSJewellery" in sent_images[0][2]
    assert "Hello, Sir/Madam! 👋" in sent_images[0][2]

    print("\nAll Stage 3 conversation tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
