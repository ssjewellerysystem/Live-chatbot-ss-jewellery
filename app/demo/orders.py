from typing import Dict, Optional
from pydantic import BaseModel

class Order(BaseModel):
    id: str
    status: str
    estimated_delivery: str
    tracking_url: Optional[str] = None
    payment_status: Optional[str] = "Paid"
    order_date: Optional[str] = "N/A"
    customer_name: Optional[str] = None

DEMO_ORDERS: Dict[str, Order] = {
    "SJ10241": Order(
        id="SJ10241",
        status="Out For Delivery",
        estimated_delivery="15 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12341"
    ),
    "SJ10242": Order(
        id="SJ10242",
        status="Shipped",
        estimated_delivery="18 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK67842"
    ),
    "SJ10243": Order(
        id="SJ10243",
        status="Processing",
        estimated_delivery="20 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK11243"
    ),
    "SJ10244": Order(
        id="SJ10244",
        status="Delivered",
        estimated_delivery="10 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK44544"
    ),
    "SJ10245": Order(
        id="SJ10245",
        status="Shipped",
        estimated_delivery="14 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK55124"
    ),
    "SJ10246": Order(
        id="SJ10246",
        status="Processing",
        estimated_delivery="22 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK98321"
    ),
    "SJ10247": Order(
        id="SJ10247",
        status="Delivered",
        estimated_delivery="05 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12347"
    ),
    "SJ10248": Order(
        id="SJ10248",
        status="Cancelled",
        estimated_delivery="N/A",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12348"
    ),
    "SJ10249": Order(
        id="SJ10249",
        status="Out For Delivery",
        estimated_delivery="12 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12349"
    ),
    "SJ10250": Order(
        id="SJ10250",
        status="Shipped",
        estimated_delivery="16 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12350"
    ),
    "SJ10251": Order(
        id="SJ10251",
        status="Processing",
        estimated_delivery="21 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12351"
    ),
    "SJ10252": Order(
        id="SJ10252",
        status="Delivered",
        estimated_delivery="08 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12352"
    ),
    "SJ10253": Order(
        id="SJ10253",
        status="Shipped",
        estimated_delivery="17 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12353"
    ),
    "SJ10254": Order(
        id="SJ10254",
        status="Processing",
        estimated_delivery="23 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12354"
    ),
    "SJ10255": Order(
        id="SJ10255",
        status="Out For Delivery",
        estimated_delivery="13 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12355"
    ),
    "SJ10256": Order(
        id="SJ10256",
        status="Delivered",
        estimated_delivery="09 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12356"
    ),
    "SJ10257": Order(
        id="SJ10257",
        status="Shipped",
        estimated_delivery="19 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12357"
    ),
    "SJ10258": Order(
        id="SJ10258",
        status="Processing",
        estimated_delivery="25 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12358"
    ),
    "SJ10259": Order(
        id="SJ10259",
        status="Returned",
        estimated_delivery="N/A",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12359"
    ),
    "SJ10260": Order(
        id="SJ10260",
        status="Delivered",
        estimated_delivery="04 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12360"
    ),
    "SJ10261": Order(
        id="SJ10261",
        status="Shipped",
        estimated_delivery="15 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12361"
    ),
    "SJ10262": Order(
        id="SJ10262",
        status="Out For Delivery",
        estimated_delivery="12 July 2026",
        tracking_url="https://demo.ssjewellery.com/orders/TRK12362"
    )
}

from app.services.url_builder import URLBuilder
for order in DEMO_ORDERS.values():
    order.tracking_url = URLBuilder.get_order_url(order.id)
