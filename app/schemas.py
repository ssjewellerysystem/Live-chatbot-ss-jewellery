from typing import List, Optional
from pydantic import BaseModel, Field


class WhatsAppProfile(BaseModel):
    name: str


class WhatsAppContact(BaseModel):
    profile: Optional[WhatsAppProfile] = None
    wa_id: str


class WhatsAppMessageText(BaseModel):
    body: str


class WhatsAppMessage(BaseModel):
    from_field: str = Field(..., alias="from")
    id: str
    timestamp: str
    text: Optional[WhatsAppMessageText] = None
    type: str


class WhatsAppStatus(BaseModel):
    id: str
    status: str
    recipient_id: str
    timestamp: str


class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: dict
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None
    statuses: Optional[List[WhatsAppStatus]] = None


class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    """
    Validates the root structure of Meta WhatsApp Webhook payloads.
    Contains entries representing updates (messages or status notifications).
    """
    object: str
    entry: List[WhatsAppEntry]


class ExtractedMessage(BaseModel):
    """
    Internal domain model containing the extracted sender details and message text.
    Provides a decoupled contract between the webhook layer and downstream clients.
    """
    sender_phone: str
    sender_name: str
    message_text: str


class Product(BaseModel):
    """
    Pydantic model representing a product from the database.
    """
    id: str
    name: str
    category: str
    price: float
    description: str
    availability: str
    image_url: str
    website_url: Optional[str] = None

