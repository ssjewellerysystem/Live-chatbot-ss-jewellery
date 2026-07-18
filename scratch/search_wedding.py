import asyncio
from app.database.connection import DatabaseConnectionManager

async def search_wedding():
    await DatabaseConnectionManager.initialize()
    try:
        rows = await DatabaseConnectionManager.fetch(
            "SELECT p.id, p.name, p.price, p.description, c.name as category_name "
            "FROM products p LEFT JOIN categories c ON p.category_id = c.id "
            "WHERE p.name ILIKE '%wedding%' OR p.description ILIKE '%wedding%' "
            "OR p.name ILIKE '%bridal%' OR p.description ILIKE '%bridal%'"
        )
        for r in rows:
            print(f"ID={r['id']}, Name={r['name']}, Price={r['price']}, Cat={r['category_name']}, Desc={r['description'][:100]}")
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(search_wedding())
