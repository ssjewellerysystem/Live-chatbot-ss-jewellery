import json
from typing import Optional
from fastapi import APIRouter, Request, Query, Header
from fastapi.responses import PlainTextResponse, JSONResponse

from app.schemas import WhatsAppWebhookPayload
from app.utils import verify_webhook, verify_signature, extract_message
from app.whatsapp_client import WhatsAppClient
from app.exceptions import InvalidPayloadError, ChatbotException
from app.services.ai_service import AIService

router = APIRouter(prefix="/webhook", tags=["Webhook"])

# Instantiate service clients
whatsapp_client = WhatsAppClient()
ai_service = AIService()


@router.get("", response_class=PlainTextResponse)
async def get_webhook_verification(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge"),
) -> str:
    """
    Handles Meta's Webhook verification GET request.
    Verifies token credentials and returns the hub challenge back to Meta.
    """
    return verify_webhook(mode, token, challenge)


@router.post("")
async def post_webhook_events(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
) -> JSONResponse:
    """
    Handles incoming webhook payloads from Meta.
    Verifies payload signature, extracts the message body, calls Gemini,
    and returns the AI generated response back to the user via WhatsApp.
    """
    # 1. Fetch raw request body for signature verification
    body_bytes = await request.body()

    # 2. Cryptographically verify signature to ensure origin integrity
    # (If signature verification fails, return 401/403 since it might be an attacker)
    verify_signature(body_bytes, x_hub_signature_256)

    # 3. Process payload and safely return 200 OK on error to prevent Meta from retrying
    try:
        # 3.1. Parse and decode JSON body
        try:
            body_json = json.loads(body_bytes.decode("utf-8"))
        except UnicodeDecodeError:
            raise InvalidPayloadError("Failed to decode payload bytes using UTF-8.")
        except json.JSONDecodeError:
            raise InvalidPayloadError("Payload is not valid JSON format.")

        # 3.2. Validate incoming payload structure
        try:
            payload = WhatsAppWebhookPayload(**body_json)
        except Exception as exc:
            raise InvalidPayloadError(f"Payload validation failed: {str(exc)}")

        # 3.3. Extract sender information and message text
        extracted = extract_message(payload)
        if not extracted:
            # Acknowledge receipts, delivery notices, and other event updates with HTTP 200 without reprocessing
            return JSONResponse(
                status_code=200,
                content={"status": "ignored", "detail": "Event type ignored (not an incoming text message)."}
            )

        # 3.4. Generate reply with AI Service (Orchestrator for Stage 2)
        ai_reply = await ai_service.process_user_message(
            message_text=extracted.message_text,
            sender_name=extracted.sender_name,
            sender_phone=extracted.sender_phone
        )
        print(f"Chatbot response to '{extracted.message_text}':\n{ai_reply}\n---")

        # 3.5. Dispatch message back to sender via Meta API
        if ai_reply:
            await whatsapp_client.send_whatsapp_message(
                recipient_phone=extracted.sender_phone,
                message_text=ai_reply
            )

        return JSONResponse(
            status_code=200,
            content={"status": "success", "detail": "Message processed and response sent."}
        )

    except ChatbotException as exc:
        print(f"ChatbotException while processing webhook: {exc.message}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message
                }
            }
        )
    except Exception as exc:
        print(f"Unexpected error while processing webhook: {str(exc)}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "type": "UnexpectedError",
                    "message": str(exc)
                }
            }
        )
