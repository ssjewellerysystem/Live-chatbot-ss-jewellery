import asyncio
import time
from app.services.conversation_service import ConversationService
from app.sessions.session_manager import UserSession

async def run_stage6_tests():
    print("Initializing Conversation Service...")
    service = ConversationService()
    
    sender_phone = "919999999999"
    sender_name = "Jane Test"

    print("\n==========================================")
    print("TEST 6.1: Category and Filter Inheritance (Example 1 & 2)")
    print("==========================================")
    
    # 1. Search for rings
    reply1 = await service.handle_message(sender_phone, "Show me rings", sender_name)
    print("User: Show me rings")
    print(f"Bot:\n{reply1}\n")
    assert "Eternity Diamond" in reply1, "Should return rings"

    # Verify rings category is stored in session context
    session: UserSession = service.session_manager.get_session(sender_phone)
    assert session.current_category == "Rings", "Category 'Rings' should be stored in context"
    assert len(session.current_products) > 0, "Products list should not be empty"

    # 2. Filter: Only gold (inherits category "Rings")
    reply2 = await service.handle_message(sender_phone, "Only gold", sender_name)
    print("User: Only gold")
    print(f"Bot:\n{reply2}\n")
    assert "Eternity Diamond" in reply2, "Should return eternity diamond gold ring"

    # 3. Filter: Under Rs. 20,000 (inherits category "Rings")
    reply3 = await service.handle_message(sender_phone, "Under Rs. 20,000", sender_name)
    print("User: Under Rs. 20,000")
    print(f"Bot:\n{reply3}\n")
    assert "Haily Ring" in reply3 or "flora set" in reply3, "Should return ring below 20,000"
    assert "Classic Solitaire" not in reply3, "Classic Solitaire is 145k and should be filtered out"


    print("\n==========================================")
    print("TEST 6.2: Product Index Image Selection (Example 3)")
    print("==========================================")
    
    # Refresh search list to have known items
    await service.handle_message(sender_phone, "Show me rings", sender_name)
    session = service.session_manager.get_session(sender_phone)
    
    # Ask for first one image
    reply_img = await service.handle_message(sender_phone, "Show image of the first one", sender_name)
    print("User: Show image of the first one")
    print(f"Bot:\n{reply_img}\n")
    assert "Eternity Diamond" in reply_img, "Should extract first ring details/caption"
    
    # Verify selected product is stored
    assert session.selected_product is not None, "Selected product should be saved in context"
    assert "Eternity Diamond" in session.selected_product.get("name"), "Selected product should be Eternity Diamond"


    print("\n==========================================")
    print("TEST 6.3: View Product Link (Example 4)")
    print("==========================================")
    
    reply_link = await service.handle_message(sender_phone, "Open that product", sender_name)
    print("User: Open that product")
    print(f"Bot:\n{reply_link}\n")
    assert "?category=Rings" in reply_link, "Should return URL of active category"
    assert reply_link.startswith("🔗 _View Product:_"), "Should match link formatting"


    print("\n==========================================")
    print("TEST 6.4: Order Status Delivery Tracking (Example 5)")
    print("==========================================")
    
    # 1. Track order
    reply_ord1 = await service.handle_message(sender_phone, "Track my order SJ10241", sender_name)
    print("User: Track my order SJ10241")
    print(f"Bot:\n{reply_ord1}\n")
    assert "SJ10241" in reply_ord1
    assert "Out For Delivery" in reply_ord1

    # Verify order is saved in session
    session = service.session_manager.get_session(sender_phone)
    assert session.current_order is not None, "Current order should be saved in session context"
    assert session.current_order.get("id") == "SJ10241", "Order ID should match"

    # 2. Ask "When will it arrive?"
    reply_ord2 = await service.handle_message(sender_phone, "When will it arrive?", sender_name)
    print("User: When will it arrive?")
    print(f"Bot:\n{reply_ord2}\n")
    # Should use saved context to return delivery details
    assert "15 July 2026" in reply_ord2 or "Out For Delivery" in reply_ord2, "Should return cached order details"


    print("\n==========================================")
    print("TEST 6.5: In-Memory Message History Limit (15 Messages)")
    print("==========================================")
    
    session = service.session_manager.get_session(sender_phone)
    
    # Send a bunch of messages to fill history
    for i in range(10):
        await service.handle_message(sender_phone, f"Dummy message {i}", sender_name)
        
    print(f"Current history length: {len(session.messages)}")
    assert len(session.messages) <= 15, "Session history must never exceed 15 messages"


    print("\n==========================================")
    print("TEST 6.6: Session Expiration Timeout (30s)")
    print("==========================================")
    
    # We started order tracking or dummy queries
    session = service.session_manager.get_session(sender_phone)
    assert len(session.messages) > 0, "History should exist before timeout"
    
    # Force timeout expiration by setting timeout to 30s and back-dating last_accessed
    service.session_manager.timeout_seconds = 30.0
    session.last_accessed = time.time() - 35.0
    
    # Fetch session again (this triggers deletion/reset in SessionManager if expired)
    expired_session = service.session_manager.get_session(sender_phone)
    assert len(expired_session.messages) == 0, "Session messages should be wiped after expiration"
    assert expired_session.current_category is None, "Context variables should be wiped after expiration"
    
    print("\nAll Stage 6 Context-Aware Temporary Memory tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_stage6_tests())
