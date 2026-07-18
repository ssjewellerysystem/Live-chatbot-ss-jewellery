import hmac
import hashlib
import json
import httpx
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.config import settings

def send_payload(message_text: str):
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
                                    "wa_id": "919829276750"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919829276750",
                                    "id": "wamid.HBgMOTE5Mjc2NzUwRlQxMjM0NTY3ODkw",
                                    "timestamp": "1783751322",
                                    "text": {
                                        "body": message_text
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
    computed_sig = hmac.new(
        key=settings.APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={computed_sig}"
    }

    print(f"\n--- Testing message: \"{message_text}\" ---")
    try:
        response = httpx.post(
            "http://127.0.0.1:8000/webhook",
            content=payload_bytes,
            headers=headers,
            timeout=15.0
        )
        print(f"Response Status Code: {response.status_code}")
        print("Response Content:")
        print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_cases = [
        "Hii",
        "Show me gold rings under 20000",
        "Show engagement rings",
        "Show earrings",
        "Show me some diamond necklaces",
        "Show me watches",
        "Track my order SJ10241",
        "Can you create a support ticket for a damaged ring?"
    ]
    for test in test_cases:
        send_payload(test)
