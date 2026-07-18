from typing import Dict, Optional
import random
from pydantic import BaseModel

class SupportTicket(BaseModel):
    ticket_id: str
    issue_summary: str
    status: str
    support_url: str
    customer_email: Optional[str] = None

# In-memory storage for tickets initialized with 20+ pre-seeded tickets
DEMO_TICKETS: Dict[str, SupportTicket] = {
    f"SUP-{1000 + i}": SupportTicket(
        ticket_id=f"SUP-{1000 + i}",
        issue_summary=summary,
        status="Closed" if i % 3 == 0 else "Open",
        support_url="https://demo.ssjewellery.com/support",
        customer_email=f"customer{i}@example.com"
    )
    for i, summary in enumerate([
        "My ring size is incorrect.",
        "Necklace clasp is loose.",
        "Tracking status has not updated in 3 days.",
        "Received earrings with a missing diamond stone.",
        "Need to change delivery address for SJ10243.",
        "Is it possible to customize the Gold Jhumka Earrings with rubies?",
        "Refund status for cancelled order SJ10248.",
        "Bangle set is too tight, need exchange.",
        "Payment got deducted twice for my last transaction.",
        "Website crashed during checkout.",
        "Do you provide certificate of authenticity for solitaire diamonds?",
        "Received a silver bracelet instead of gold chain.",
        "Requesting invoice copy for SJ10244.",
        "How do I clean my silver ornaments?",
        "Can I get gift packaging for my order?",
        "Coupon code SSJNEW10 is not working.",
        "Delivery executive was rude and didn't deliver order.",
        "Pendant chain length is too short.",
        "Is cash on delivery available for orders above 50,000?",
        "Need help with selecting an engagement ring.",
        "Do you ship internationally to USA?",
        "Damaged packaging received."
    ])
}

def create_demo_ticket(issue_summary: str, customer_email: Optional[str] = None) -> SupportTicket:
    """
    Creates a new support ticket in the in-memory database with a random ID.
    """
    ticket_num = random.randint(2000, 9999)
    ticket_id = f"SUP-{ticket_num}"
    
    from app.services.url_builder import URLBuilder
    ticket = SupportTicket(
        ticket_id=ticket_id,
        issue_summary=issue_summary,
        status="Open",
        support_url=URLBuilder.get_support_url(),
        customer_email=customer_email
    )
    
    DEMO_TICKETS[ticket_id] = ticket
    return ticket

from app.services.url_builder import URLBuilder
for ticket in DEMO_TICKETS.values():
    ticket.support_url = URLBuilder.get_support_url()
