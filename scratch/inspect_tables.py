import asyncio
from app.database.connection import DatabaseConnectionManager

async def main():
    await DatabaseConnectionManager.initialize()
    try:
        # Get list of tables
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        rows = await DatabaseConnectionManager.fetch(query)
        print("Tables in database:")
        for r in rows:
            print(f"- {r['table_name']}")
            
        # Get columns of 'users' table if it exists
        query_users = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """
        rows_users = await DatabaseConnectionManager.fetch(query_users)
        if rows_users:
            print("\nColumns in 'users' table:")
            for r in rows_users:
                print(f"- {r['column_name']} ({r['data_type']})")
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(main())
