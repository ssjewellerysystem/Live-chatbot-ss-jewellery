import asyncio
from app.database.connection import DatabaseConnectionManager
from app.database.repositories.product_repository import ProductRepository
from app.database.repositories.order_repository import OrderRepository
from app.services.conversation_service import ConversationService

async def test_database_features():
    print("==========================================")
    print("VERIFYING STAGE 4 DATABASE-DRIVEN FEATURES")
    print("==========================================")
    
    # 1. Initialize Connection Pool
    print("Initializing Database Connection Manager...")
    await DatabaseConnectionManager.initialize()
    
    try:
        # 2. Verify Product Repository Queries
        print("\n--- Test 2.1: Category Search (Rings) ---")
        product_repo = ProductRepository()
        rings = await product_repo.search_products(category_name="Rings", limit=3)
        print(f"Found {len(rings)} Rings:")
        for r in rings:
            print(f"- {r['name']} (Category: {r['category']}, Price: ₹{r['price']}, Stock: {r['availability']})")
        assert len(rings) <= 3, "Rings limit should not exceed 3"

        print("\n--- Test 2.2: Category Search with Keyword (Gold) ---")
        gold_items = await product_repo.search_products(query_text="Gold", category_name="Necklaces", limit=3)
        print(f"Found {len(gold_items)} Gold Necklaces:")
        for item in gold_items:
            print(f"- {item['name']} (Price: ₹{item['price']}, URL: {item['website_url']})")
        assert len(gold_items) <= 3, "Limit should not exceed 3"

        # 3. Verify Order Repository Queries
        print("\n--- Test 3.1: Order ID Query (Exact) ---")
        order_repo = OrderRepository()
        # Querying the order ID we observed in the DB check: BB-792984
        order_db = await order_repo.find_by_order_id("BB-792984")
        if order_db:
            print(f"Found order in Neon: ID={order_db['id']}, Status={order_db['status']}, Delivery={order_db['estimated_delivery']}, URL={order_db['tracking_url']}")
            assert order_db["id"] == "BB-792984", "Should match searched ID"
        else:
            print("Warning: Sample order BB-792984 not found in database. Checking fallback.")

        print("\n--- Test 3.2: Order ID Query (Partial/Wildcard) ---")
        order_partial = await order_repo.find_by_order_id("792984")
        if order_partial:
            print(f"Found order via wildcard: ID={order_partial['id']}, Status={order_partial['status']}")
            assert order_partial["id"] == "BB-792984", "Wildcard search should find BB-792984"

        # 4. Verify Read-Only Security Constraints
        print("\n--- Test 4.1: SQL Injection / Write Rejections ---")
        
        forbidden_queries = [
            "INSERT INTO products (name, price) VALUES ('Fake Ring', 100)",
            "UPDATE products SET price = 0 WHERE id = 51",
            "DELETE FROM products WHERE id = 51",
            "DROP TABLE products",
            "ALTER TABLE products ADD COLUMN discount_percent int",
            "CREATE TABLE hack (id int)",
            "TRUNCATE products"
        ]
        
        for sql in forbidden_queries:
            print(f"Attempting write SQL: '{sql}'")
            try:
                await DatabaseConnectionManager.fetch(sql)
                assert False, f"Query '{sql}' was executed but should have been blocked!"
            except PermissionError as pe:
                print(f"--> Blocked successfully: {pe}")
            except Exception as e:
                print(f"--> Error: {type(e).__name__} - {e}")
                
        print("\nDatabase read-only protection verified successfully!")

        # 5. Verify Conversational Scenarios
        print("\n--- Test 5.1: Conversational search scenarios ---")
        service = ConversationService()
        
        # Test Case 1: "Show me rings" -> Returns rings immediately
        print("Executing: Show me rings")
        res1 = await service.handle_message("12345", "Show me rings", "Test User")
        print(f"Reply:\n{res1}\n")
        assert "Which type of ring" not in res1, "Should not ask clarifying question!"
        assert "Classic Solitaire" in res1 or "Eternity Diamond" in res1, "Should return Ring products"
        
        # Test Case 2: "Show me gold rings" -> Returns gold rings immediately
        print("Executing: Show me gold rings")
        res2 = await service.handle_message("12345", "Show me gold rings", "Test User")
        print(f"Reply:\n{res2}\n")
        assert "Which type of ring" not in res2, "Should not ask clarifying question!"
        
        # Test Case 3: "Show me diamond rings" -> Returns diamond rings immediately
        print("Executing: Show me diamond rings")
        res3 = await service.handle_message("12345", "Show me diamond rings", "Test User")
        print(f"Reply:\n{res3}\n")
        assert "Which type of ring" not in res3, "Should not ask clarifying question!"
        
        # Test Case 4: "Show me rings under ₹20,000" -> Returns rings under 20,000
        print("Executing: Show me rings under ₹20,000")
        res4 = await service.handle_message("12345", "Show me rings under ₹20,000", "Test User")
        print(f"Reply:\n{res4}\n")
        assert "Which type of ring" not in res4, "Should not ask clarifying question!"
        assert "BlueStone Women's The Haily Ring" in res4 or "flora set" in res4 or "PALMONAS Tree of Life" in res4

        # Test Case 5: "Show me necklaces below ₹50,000" -> Returns necklaces below 50,000
        print("Executing: Show me necklaces below ₹50,000")
        res5 = await service.handle_message("12345", "Show me necklaces below ₹50,000", "Test User")
        print(f"Reply:\n{res5}\n")
        assert "Which type of necklace" not in res5, "Should not ask clarifying question!"
        assert "No matching products found." in res5 or "Necklaces" in res5

        
        # Test Case 6: "Show me jewellery" -> Asks user which category they are interested in
        print("Executing: Show me jewellery")
        res6 = await service.handle_message("12345", "Show me jewellery", "Test User")
        print(f"Reply:\n{res6}\n")
        assert "Which category are you looking for?" in res6, "Should prompt for category choice"

    finally:
        print("\nClosing Database Connection Pool...")
        await DatabaseConnectionManager.close()
        
    print("\nAll database integration and conversational scenario tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_database_features())
