import asyncio
from app.database.connection import DatabaseConnectionManager

async def main():
    await DatabaseConnectionManager.initialize()
    try:
        # Check count of transactions
        count_tx = await DatabaseConnectionManager.fetchval("SELECT COUNT(*) FROM transactions")
        print(f"Total transactions: {count_tx}")
        if count_tx > 0:
            rows = await DatabaseConnectionManager.fetch("SELECT * FROM transactions LIMIT 5")
            for r in rows:
                print(dict(r))
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(main())
