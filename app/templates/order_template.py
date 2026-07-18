from app.demo.orders import Order
from app.services.url_builder import URLBuilder

def format_ask_order_id(sender_name: str) -> str:
    """
    Format the follow-up question asking for an Order ID.
    """
    return (
        "📦 Please enter your Order ID.\n\n"
        "Example:\n"
        "SJ10245"
    )

def format_order_status(order: Order) -> str:
    """
    Formats the order details into a friendly response.
    """
    est_delivery = order.estimated_delivery or "N/A"
    order_date = getattr(order, "order_date", "12 July 2026") or "N/A"
    payment = getattr(order, "payment_status", "Paid") or "Paid"
    status = order.status or "Pending"
    
    # Optional customer name display (only if available and not encrypted)
    cust_name = getattr(order, "customer_name", None)
    cust_name_str = f"Customer Name: {cust_name}\n" if cust_name and not cust_name.startswith("BB_ENC:") else ""

    return (
        f"📦 Order Status Details\n"
        f"Order ID: {order.id}\n"
        f"{cust_name_str}"
        f"Status: {status}\n"
        f"Payment: {payment}\n"
        f"Order Date: {order_date}\n"
        f"Estimated Delivery: {est_delivery}\n\n"
        f"🔗 Visit Website\n"
        f"{URLBuilder.get_website_url()}"
    )

def format_order_not_found(order_id: str, sender_name: str) -> str:
    """
    Formats the response when an order ID is invalid or not found.
    """
    return (
        "❌ We couldn't find an order with this Order ID.\n"
        "Please check the Order ID and try again."
    )
