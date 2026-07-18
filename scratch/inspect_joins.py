import asyncio
from app.database.connection import DatabaseConnectionManager

async def main():
    await DatabaseConnectionManager.initialize()
    try:
        # Fetch some joined order data
        query = """
            SELECT 
                o.id AS internal_id,
                o.order_id,
                o.status AS order_status,
                o.created_at AS order_date,
                o.delivery_date,
                u.full_name AS customer_name,
                t.status AS payment_status
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN transactions t ON o.id = t.order_id
            LIMIT 5
        """
        rows = await DatabaseConnectionManager.fetch(query)
        for r in rows:
            print(dict(r))
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(main())
