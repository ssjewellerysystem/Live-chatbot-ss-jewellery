import asyncio
from app.services.product_service import ProductService

async def main():
    service = ProductService()
    cats = await service.get_categories()
    print("Categories:", cats)
    matched = service.match_categories("Wedding jewellery under 50000", cats)
    print("Matched for 'Wedding jewellery under 50000':", matched)

if __name__ == "__main__":
    asyncio.run(main())
