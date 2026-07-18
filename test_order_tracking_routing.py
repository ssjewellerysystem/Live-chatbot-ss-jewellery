import asyncio
from app.services.conversation_service import ConversationService
from app.database.connection import DatabaseConnectionManager

async def test_order_tracking_routing():
    print("==========================================")
    print("VERIFYING ORDER TRACKING INTENT ROUTING")
    print("==========================================")
    
    # 1. Initialize Connection Pool
    print("Initializing Database Connection Manager...")
    await DatabaseConnectionManager.initialize()
    
    try:
        service = ConversationService()
        sender_phone = "919999999999"
        sender_name = "Irshad Mohammad"
        
        phrases = [
            "Track my order",
            "Order status",
            "Check my order",
            "Where is my order?",
            "Order tracking",
            "Track order",
            "Track order status",
            "Check order status",
            "My order",
            "Delivery status",
            "Shipment status",
            "Order update",
            "Track package",
            "Where is my package?",
            "I want to track my order",
            "Check my shipment",
            "Order details",
            "My delivery"
        ]
        
        expected_substrings = [
            "📦 Please enter your Order ID.",
            "Example:",
            "SJ10245"
        ]
        
        for phrase in phrases:
            # Get clean session for each run
            session = service.session_manager.get_session(sender_phone)
            session.reset_completely()
            
            print(f"\nUser: '{phrase}'")
            reply = await service.handle_message(sender_phone, phrase, sender_name)
            print(f"Bot:\n{reply}")
            
            # Assertions
            for expected in expected_substrings:
                assert expected in reply, f"Response for phrase '{phrase}' missing: '{expected}'"
                
        print("\nAll order tracking phrases successfully routed to ORDER_TRACKING intent and prompted correctly!")
        
        # Test Case: If an active order session already exists, continue the existing flow
        print("\n--- Testing Active Order Session Preservation ---")
        session = service.session_manager.get_session(sender_phone)
        session.reset_completely()
        
        # 1. Track order with a valid order ID
        print("User: Track my order SJ10241")
        reply_track = await service.handle_message(sender_phone, "Track my order SJ10241", sender_name)
        print(f"Bot:\n{reply_track}")
        assert "SJ10241" in reply_track, "Should output status of SJ10241"
        assert "Payment: Paid" in reply_track, "Should show payment status"
        assert "Order Date:" in reply_track, "Should show order date"
        assert "🔗 Visit Website" in reply_track, "Should show website link"
        
        # 2. Ask "Order status" again (without ID)
        print("\nUser: Order status")
        reply_again = await service.handle_message(sender_phone, "Order status", sender_name)
        print(f"Bot:\n{reply_again}")
        assert "SJ10241" in reply_again, "Should return cached order details immediately without asking for ID"
        assert "📦 Please enter your Order ID." not in reply_again, "Should NOT ask for the Order ID again since active session exists"

        # Test Case: Track an order from Neon PostgreSQL
        print("\n--- Testing Neon PostgreSQL order lookup ---")
        session = service.session_manager.get_session(sender_phone)
        session.reset_completely()
        
        print("User: BB-792984")
        reply_db = await service.handle_message(sender_phone, "BB-792984", sender_name)
        print(f"Bot:\n{reply_db}")
        assert "BB-792984" in reply_db, "Should output status of BB-792984"
        assert "Status: Delivered" in reply_db, "Should match status from Neon"
        assert "Estimated Delivery: 10 July 2026" in reply_db, "Should match delivery date from Neon"
        assert "Order Date: 05 July 2026" in reply_db, "Should format and match created_at date from Neon"
        assert "Payment: Paid" in reply_db, "Should show payment status (default or fetched)"
        assert "🔗 Visit Website" in reply_db, "Should show website link"

        # Test Case: Handle invalid Order ID
        print("\n--- Testing Invalid Order ID ---")
        session = service.session_manager.get_session(sender_phone)
        session.reset_completely()
        session.current_flow = "order_tracking"
        session.current_step = "waiting_order_id"
        
        print("User: INVALID123")
        reply_invalid = await service.handle_message(sender_phone, "INVALID123", sender_name)
        print(f"Bot:\n{reply_invalid}")
        assert "❌ We couldn't find an order with this Order ID." in reply_invalid, "Should output not found error"
        assert "Please check the Order ID and try again." in reply_invalid, "Should output instructions"

        print("\nAll database tracking features verified successfully!")

    finally:
        print("\nClosing Database Connection Pool...")
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(test_order_tracking_routing())
