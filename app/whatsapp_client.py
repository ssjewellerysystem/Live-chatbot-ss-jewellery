import httpx
from typing import Optional
from app.config import settings
from app.exceptions import WhatsAppAPIError



class WhatsAppClient:
    """
    Client for interacting with the Meta WhatsApp Cloud API.
    Handles authentication headers and sending messages asynchronously.
    """
    def __init__(self) -> None:
        self.base_url = f"https://graph.facebook.com/v20.0/{settings.PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        """
        Closes the underlying HTTP client.
        """
        await self.client.aclose()

    async def send_whatsapp_message(self, recipient_phone: str, message_text: str) -> dict:
        """
        Sends a text message to a WhatsApp user.
        Raises WhatsAppAPIError if the API request fails or returns an error.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        try:
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers=self.headers
            )
            response_data = response.json()
        except httpx.HTTPStatusError as exc:
            raise WhatsAppAPIError(f"HTTP error status: {exc.response.status_code}")
        except httpx.RequestError as exc:
            raise WhatsAppAPIError(f"Request connection failed: {str(exc)}")
        except Exception as exc:
            raise WhatsAppAPIError(f"Unexpected error: {str(exc)}")

        if response.status_code != 200:
            error_msg = response_data.get("error", {}).get("message", "Unknown Meta API error")
            raise WhatsAppAPIError(error_msg, status_code=response.status_code)

        return response_data

    async def send_image_message(self, recipient_phone: str, image_url: str, caption: Optional[str] = None) -> dict:
        """
        Sends an image message to a WhatsApp user using the image URL.
        Optionally attaches a caption to send image and details in a single message.
        Raises WhatsAppAPIError if the API request fails or returns an error.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        if caption:
            payload["image"]["caption"] = caption

        try:
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers=self.headers
            )
            response_data = response.json()
            print(f"Meta API Response Status Code for Image request: {response.status_code}")
            print(f"Meta API Response Body for Image request: {response.text}")
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error during image dispatch. Status Code: {exc.response.status_code}")
            print(f"Response Body: {exc.response.text}")
            raise WhatsAppAPIError(f"HTTP error status: {exc.response.status_code}")
        except httpx.RequestError as exc:
            print(f"Request connection failed for image dispatch: {str(exc)}")
            raise WhatsAppAPIError(f"Request connection failed: {str(exc)}")
        except Exception as exc:
            print(f"Unexpected error during image dispatch: {str(exc)}")
            raise WhatsAppAPIError(f"Unexpected error: {str(exc)}")

        if response.status_code != 200:
            print(f"Meta API Rejected Image. HTTP Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            error_msg = response_data.get("error", {}).get("message", "Unknown Meta API error")
            raise WhatsAppAPIError(error_msg, status_code=response.status_code)

        return response_data
