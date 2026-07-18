import hashlib
import hmac
from typing import Optional
from app.config import settings
from app.exceptions import WebhookVerificationError, SignatureVerificationError
from app.schemas import WhatsAppWebhookPayload, ExtractedMessage


def verify_webhook(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> str:
    """
    Verifies the webhook subscription handshake from Meta.
    Returns the hub.challenge if the verify_token matches ours,
    otherwise raises a WebhookVerificationError.
    """
    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        if challenge:
            return challenge
        raise WebhookVerificationError("Verification challenge is missing.")
    raise WebhookVerificationError("Verification token or mode mismatch.")


def verify_signature(payload_bytes: bytes, signature_header: Optional[str]) -> None:
    """
    Verifies the HMAC SHA-256 signature of the incoming request from Meta
    using our APP_SECRET to prevent spoofing.
    Raises SignatureVerificationError if signature is missing or incorrect.
    """
    if not signature_header:
        raise SignatureVerificationError("Missing X-Hub-Signature-256 header.")

    if not signature_header.startswith("sha256="):
        raise SignatureVerificationError("Invalid signature header format.")

    try:
        received_sig = signature_header.split("sha256=")[1]
    except IndexError:
        raise SignatureVerificationError("Invalid signature header format.")

    computed_sig = hmac.new(
        key=settings.APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_sig, computed_sig):
        raise SignatureVerificationError("HMAC Signature verification failed.")


def extract_message(payload: WhatsAppWebhookPayload) -> Optional[ExtractedMessage]:
    """
    Parses a validated webhook payload and extracts essential information:
    - Sender phone number (wa_id / from_field)
    - Sender profile name
    - Message body text
    
    Returns None if the payload does not contain a text message (e.g. status updates).
    """
    if not payload.entry:
        return None

    for entry in payload.entry:
        if not entry.changes:
            continue
        for change in entry.changes:
            value = change.value
            
            # Status updates (delivered, read receipts, etc.) do not contain messages
            if not value.messages:
                continue

            for msg in value.messages:
                # Stage 1 only processes incoming text messages
                if msg.type != "text" or not msg.text:
                    continue

                # Locate corresponding contact name if available
                sender_name = "WhatsApp User"
                if value.contacts:
                    for contact in value.contacts:
                        if contact.wa_id == msg.from_field and contact.profile:
                            sender_name = contact.profile.name
                            break

                return ExtractedMessage(
                    sender_phone=msg.from_field,
                    sender_name=sender_name,
                    message_text=msg.text.body
                )
    return None
