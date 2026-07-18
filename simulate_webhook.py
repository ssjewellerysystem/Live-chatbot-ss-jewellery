import hmac
import hashlib
import json
import httpx

# Read settings from Pydantic settings by importing config
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.config import settings

def run_simulation():
    # 1. Define the payload matching Meta's structure
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1515795013427026",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "918302996248",
                                "phone_number_id": settings.PHONE_NUMBER_ID
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Irshad Mohammad"
                                    },
                                    "wa_id": "919829276750",
                                    "user_id": "IN.2532435220604858"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919829276750",
                                    "from_user_id": "IN.2532435220604858",
                                    "id": "wamid.HBgMOTE5Mjc2NzUwRlQxMjM0NTY3ODkw",
                                    "timestamp": "1783751322",
                                    "text": {
                                        "body": "Show me rings"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    payload_bytes = json.dumps(payload).encode("utf-8")

    # 2. Compute HMAC SHA-256 signature using APP_SECRET
    computed_sig = hmac.new(
        key=settings.APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    signature_header = f"sha256={computed_sig}"
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature_header
    }

    print("Sending webhook payload to local server...")
    try:
        response = httpx.post(
            "http://127.0.0.1:8000/webhook",
            content=payload_bytes,
            headers=headers,
            timeout=15.0
        )
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(response.json())
    except Exception as e:
        print("Failed to send request or retrieve response:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simulation()
