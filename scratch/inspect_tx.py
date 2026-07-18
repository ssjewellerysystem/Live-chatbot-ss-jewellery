import asyncio
from app.database.connection import DatabaseConnectionManager

async def main():
    await DatabaseConnectionManager.initialize()
    try:
        # Get columns of 'transactions' table
        query_tx = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'transactions'
        """
        rows_tx = await DatabaseConnectionManager.fetch(query_tx)
        print("Columns in 'transactions' table:")
        for r in rows_tx:
            print(f"- {r['column_name']} ({r['data_type']})")
            
        # Get columns of 'order_items' table
        query_items = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'order_items'
        """
        rows_items = await DatabaseConnectionManager.fetch(query_items)
        print("\nColumns in 'order_items' table:")
        for r in rows_items:
            print(f"- {r['column_name']} ({r['data_type']})")
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(main())
