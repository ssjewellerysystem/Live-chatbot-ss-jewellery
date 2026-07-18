from app.demo.tickets import SupportTicket

def format_ask_support_issue() -> str:
    """
    Prompts the user to describe their issue.
    """
    return "Please briefly describe your issue."

def format_ask_support_email() -> str:
    """
    Prompts the user to enter their email address.
    """
    return "Please enter your email address."

def format_invalid_email() -> str:
    """
    Prompts when the email address validation fails.
    """
    return "That email address format doesn't look quite right. Please enter a valid email address (e.g., name@example.com)."

def format_support_ticket_created(ticket: SupportTicket) -> str:
    """
    Formats the created support ticket response.
    """
    return (
        f"🎫 *Support Ticket Created*\n\n"
        f"• *Ticket ID:* {ticket.ticket_id}\n"
        f"• *Status:* {ticket.status}\n"
        f"• *Issue:* {ticket.issue_summary}\n"
        f"• *Email:* {ticket.customer_email}\n\n"
        f"We have registered your support request. A support agent will contact you soon.\n"
        f"🔗 _Support Center:_ {ticket.support_url}"
    )
