import asyncio
from app.services.intent_service import IntentService
from app.config import settings

async def main():
    service = IntentService()
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
    print("Testing phrases:")
    for phrase in phrases:
        try:
            res = await service.detect_intent(phrase)
            print(f"Phrase: '{phrase}' -> Intent: {res.intent}, Entity: '{res.extracted_entity}'")
        except Exception as e:
            print(f"Phrase: '{phrase}' -> Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
