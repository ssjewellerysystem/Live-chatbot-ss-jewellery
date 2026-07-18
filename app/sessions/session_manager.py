import time
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.config import settings

class UserSession(BaseModel):
    phone_number: str
    current_flow: Optional[str] = None          # e.g. "order_tracking", "support_ticket", "product_search"
    current_step: Optional[str] = None          # e.g. "waiting_order_id", "waiting_issue", "waiting_email", "waiting_ring_type"
    data: Dict[str, Any] = Field(default_factory=dict)  # temporary collected data
    last_accessed: float = Field(default_factory=time.time)

    # Context Aware Memory
    messages: List[Dict[str, str]] = Field(default_factory=list)  # List of {"role": "user"|"assistant", "text": str}
    current_category: Optional[str] = None
    current_products: List[dict] = Field(default_factory=list)  # Filtered/active product results
    base_products: List[dict] = Field(default_factory=list)     # Unfiltered base product search results from database
    selected_product: Optional[dict] = None
    current_order: Optional[dict] = None
    current_intent: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_gold: Optional[bool] = None
    is_silver: Optional[bool] = None
    is_diamond: Optional[bool] = None
    current_page: int = 1
    category_distribution: Optional[dict] = None
    target_categories: List[str] = Field(default_factory=list)

    def update_access(self) -> None:
        self.last_accessed = time.time()

    def is_expired(self, timeout_seconds: float) -> bool:
        return (time.time() - self.last_accessed) > timeout_seconds

    def add_message(self, role: str, text: str) -> None:
        """Add a message to the history and keep only the latest 15 messages."""
        self.messages.append({"role": role, "text": text})
        if len(self.messages) > 15:
            self.messages = self.messages[-15:]
        self.update_access()

    def reset(self) -> None:
        """Reset the active flow state but keep the phone number and messages list."""
        self.current_flow = None
        self.current_step = None
        self.data = {}
        self.update_access()

    def reset_completely(self) -> None:
        """Completely wipes the session."""
        self.reset()
        self.messages = []
        self.current_category = None
        self.current_products = []
        self.base_products = []
        self.selected_product = None
        self.current_order = None
        self.current_intent = None
        self.min_price = None
        self.max_price = None
        self.is_gold = None
        self.is_silver = None
        self.is_diamond = None
        self.current_page = 1
        self.category_distribution = None
        self.target_categories = []
        self.update_access()

    def get_structured_context(self) -> Dict[str, Any]:
        """
        Returns the structured conversation context.
        """
        return {
            "Current Intent": self.current_flow.upper() if self.current_flow else (self.current_intent or "None"),
            "Current Product Category": self.current_category or "None",
            "Current Product List": [p.get("name") for p in self.current_products] if self.current_products else [],
            "Current Product Page": self.data.get("current_page", 1),
            "Current Selected Product": self.selected_product if self.selected_product else None,
            "Current Order": self.current_order,
            "Current Support Flow": {
                "flow": self.current_flow,
                "step": self.current_step,
                "data": self.data
            } if self.current_flow == "support_ticket" else None,
            "Current Filters": {
                "min_price": self.min_price,
                "max_price": self.max_price,
                "is_gold": self.is_gold,
                "is_silver": self.is_silver,
                "is_diamond": self.is_diamond,
            },
            "Current Price Range": f"₹{self.min_price or 0} - ₹{self.max_price or 'Any'}",
            "Current Conversation State": f"Flow: {self.current_flow or 'None'}, Step: {self.current_step or 'None'}",
            "Current Search Keywords": self.data.get("search_keywords", []),
            "Current Product Results Count": len(self.current_products)
        }


class SessionManager:
    """
    Manages in-memory user sessions.
    Implements expiration timeouts per session based on settings.
    """
    def __init__(self, timeout_seconds: Optional[float] = None) -> None:
        self.sessions: Dict[str, UserSession] = {}
        # Load timeout dynamically from env/settings (default 30 seconds)
        self.timeout_seconds = timeout_seconds or float(settings.SESSION_TIMEOUT_SECONDS)

    def get_session(self, phone_number: str) -> UserSession:
        """
        Retrieves an active session for the given phone number.
        If the session does not exist or has expired, creates a fresh session.
        """
        session = self.sessions.get(phone_number)
        
        if not session:
            session = UserSession(phone_number=phone_number)
            self.sessions[phone_number] = session
        elif session.is_expired(self.timeout_seconds):
            print(f"Session for {phone_number} has expired. Deleting and recreating session.")
            session = UserSession(phone_number=phone_number)
            self.sessions[phone_number] = session
        
        session.update_access()
        return session

    def reset_session(self, phone_number: str) -> None:
        """
        Force resets the session for a user.
        """
        if phone_number in self.sessions:
            self.sessions[phone_number].reset_completely()

    def cleanup_expired_sessions(self) -> None:
        """
        Removes/resets expired sessions to free up memory.
        """
        now = time.time()
        for phone, session in list(self.sessions.items()):
            if now - session.last_accessed > self.timeout_seconds:
                self.sessions.pop(phone, None)
