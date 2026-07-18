import asyncio
from app.database.connection import DatabaseConnectionManager

async def main():
    await DatabaseConnectionManager.initialize()
    try:
        rows = await DatabaseConnectionManager.fetch("SELECT * FROM categories")
        print("Categories:")
        for r in rows:
            print(dict(r))
    finally:
        await DatabaseConnectionManager.close()

if __name__ == "__main__":
    asyncio.run(main())
