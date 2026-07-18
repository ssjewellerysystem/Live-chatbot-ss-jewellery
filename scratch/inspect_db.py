import asyncio
from app.database.connection import DatabaseConnectionManager

async def inspect_db():
    await DatabaseConnectionManager.initialize()
    try:
        categories = await DatabaseConnectionManager.fetch("SELECT * FROM categories")
        print("=== CATEGORIES ===")
        for c in categories:
            print(c)
            
        products = await DatabaseConnectionManager.fetch(
            "SELECT p.id, p.name, p.price, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id LIMIT 20"
        )
        print("\n=== PRODUCTS ===")
        for p in products:
            print(p)
            
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(inspect_db())
