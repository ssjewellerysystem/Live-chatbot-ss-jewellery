import asyncio
import os
import sys
import httpx

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.config import settings
from app.whatsapp_client import WhatsAppClient

async def main():
    print("Welcome Logo Diagnostic & Verification Test")
    print("------------------------------------------")
    print("Settings:")
    print(f"PHONE_NUMBER_ID: {settings.PHONE_NUMBER_ID}")
    print(f"WELCOME_LOGO_URL: {settings.WELCOME_LOGO_URL}")
    print(f"WELCOME_LOGO_CAPTION: {settings.WELCOME_LOGO_CAPTION}")
    
    recipient = "919829276750"
    print(f"Recipient: {recipient}")
    
    client = WhatsAppClient()
    
    # Construct payload manually to print it
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "image",
        "image": {
            "link": settings.WELCOME_LOGO_URL.strip()
        }
    }
    if settings.WELCOME_LOGO_CAPTION:
        payload["image"]["caption"] = settings.WELCOME_LOGO_CAPTION
        
    print("\nRequest Details:")
    print(f"URL: {client.base_url}")
    print(f"Headers: {client.headers}")
    print(f"Payload: {payload}")
    
    print("\nSending request to Meta API...")
    try:
        response = await client.client.post(
            client.base_url,
            json=payload,
            headers=client.headers
        )
        print("\nResponse Details:")
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        print("Body:")
        print(response.text)
    except Exception as e:
        print("Failed to dispatch request:")
        import traceback
        traceback.print_exc()
        
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
