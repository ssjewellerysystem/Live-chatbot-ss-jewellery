import re
from typing import Optional
from app.demo.orders import Order
from app.database.repositories.order_repository import OrderRepository

class OrderService:
    """
    Service to fetch order status.
    Delegates SQL operations to the OrderRepository.
    """
    def __init__(self):
        self.repository = OrderRepository()

    async def get_order_status(self, order_query: str) -> Optional[Order]:
        """
        Retrieves order status by querying the database repository.
        """
        if not order_query:
            return None

        # Clean query
        query_clean = order_query.strip().upper()

        # Check for digits/numbers (e.g. "10245" from "SJ10245" or "792984" from "BB-792984")
        digits_match = re.search(r'\d+', query_clean)
        lookup_val = digits_match.group() if digits_match else query_clean

        # Retrieve order from repository
        order_dict = await self.repository.find_by_order_id(lookup_val)
        if not order_dict:
            # Fallback to direct search with the full raw string in case it's non-numeric
            order_dict = await self.repository.find_by_order_id(query_clean)

        if order_dict:
            return Order(**order_dict)

        return None
