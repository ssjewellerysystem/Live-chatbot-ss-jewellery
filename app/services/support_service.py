from typing import Optional
from app.demo.tickets import SupportTicket, create_demo_ticket

class SupportService:
    """
    Service to handle support ticket creation.
    Designed for seamless future integration with helpdesk APIs (Zendesk, Freshdesk, etc.).
    """
    async def create_ticket(self, issue_summary: str, customer_email: Optional[str] = None) -> SupportTicket:
        """
        Creates a support ticket for the user.
        """
        # Handle empty/short summaries gracefully
        summary = issue_summary.strip() if issue_summary else "General Support Ticket"
        if len(summary) < 5:
            summary = f"Customer Query: {summary}"
            
        ticket = create_demo_ticket(summary, customer_email)
        return ticket
