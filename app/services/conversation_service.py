import re
from typing import Optional, List, Dict, Any
from app.config import settings
from app.sessions.session_manager import SessionManager, UserSession
from app.services.intent_service import IntentService, IntentAnalysis
from app.services.url_builder import URLBuilder
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.demo.orders import Order
from app.services.support_service import SupportService
from app.services.image_response_builder import ImageResponseBuilder
from app.ai_client import GeminiClient
from app.exceptions import DatabaseConnectionError

# Import response templates
from app.templates.greeting_template import format_greeting
from app.templates.product_template import format_product_clarification, format_products_list, format_no_products_found
from app.templates.order_template import format_ask_order_id, format_order_status, format_order_not_found
from app.templates.support_template import (
    format_ask_support_issue,
    format_ask_support_email,
    format_invalid_email,
    format_support_ticket_created
)

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class ConversationService:
    """
    Core flow manager that tracks and directs conversation state step-by-step.
    Frees up the Webhook logic from handling state transitions directly.
    """
    def __init__(self) -> None:
        # Load timeout dynamically from settings
        self.session_manager = SessionManager()
        self.intent_service = IntentService()
        self.product_service = ProductService()
        self.order_service = OrderService()
        self.support_service = SupportService()
        self.gemini_client = GeminiClient()
        self.image_response_builder = ImageResponseBuilder()

    def _get_products_for_page(self, filtered_products: List[dict], target_categories: List[str], page: int, session: UserSession) -> List[dict]:
        # Group products by category
        products_by_category = {}
        for p in filtered_products:
            cat = p.get("category", "Uncategorized")
            # We want to match categories case-insensitively
            matched_cat = None
            for target_cat in target_categories:
                if target_cat.lower() == cat.lower():
                    matched_cat = target_cat
                    break
            # If target_categories is empty (generic search), group by its own category
            group_key = matched_cat or cat
            if group_key not in products_by_category:
                products_by_category[group_key] = []
            products_by_category[group_key].append(p)

        num_cats = len(target_categories)
        selected_products = []

        if num_cats == 0:
            # Generic search with no specified categories: return 3 products per page
            start = (page - 1) * 3
            end = page * 3
            selected_products = filtered_products[start:end]

        elif num_cats == 1:
            cat = target_categories[0]
            cat_list = products_by_category.get(cat, [])
            start = (page - 1) * 3
            end = page * 3
            selected_products = cat_list[start:end]

        elif num_cats == 2:
            cat_A = target_categories[0]
            cat_B = target_categories[1]
            cat_list_A = products_by_category.get(cat_A, [])
            cat_list_B = products_by_category.get(cat_B, [])

            # Determine or load distribution
            dist = session.category_distribution
            if not dist:
                avail_A = len(cat_list_A)
                avail_B = len(cat_list_B)
                if avail_A >= 2 and avail_B >= 1:
                    dist = {cat_A: 2, cat_B: 1}
                elif avail_B >= 2 and avail_A >= 1:
                    dist = {cat_A: 1, cat_B: 2}
                elif avail_A > 0 and avail_B == 0:
                    dist = {cat_A: 3, cat_B: 0}
                elif avail_B > 0 and avail_A == 0:
                    dist = {cat_A: 0, cat_B: 3}
                else:
                    # fallback distribution
                    dist = {cat_A: 2, cat_B: 1}
                session.category_distribution = dist

            start_A = (page - 1) * dist.get(cat_A, 0)
            end_A = page * dist.get(cat_A, 0)
            start_B = (page - 1) * dist.get(cat_B, 0)
            end_B = page * dist.get(cat_B, 0)

            # Get slice from A and B
            selected_products = cat_list_A[start_A:end_A] + cat_list_B[start_B:end_B]

        elif num_cats == 3 or num_cats == 4:
            # Exactly 1 product from each category per page
            for cat in target_categories:
                cat_list = products_by_category.get(cat, [])
                idx = page - 1
                if idx < len(cat_list):
                    selected_products.append(cat_list[idx])

        else:  # 5 or more categories
            # Maximum 5 products. Only ONE featured product from each category.
            # We take the first 5 categories (or those that have products)
            cats_to_use = target_categories[:5]
            for cat in cats_to_use:
                cat_list = products_by_category.get(cat, [])
                idx = page - 1
                if idx < len(cat_list):
                    selected_products.append(cat_list[idx])

        return selected_products
    async def _handle_category_list(self, session: UserSession) -> str:
        """
        Dynamically fetches categories from PostgreSQL and formats a category listing response.
        """
        # Clear previous search filters on initiating a new category list flow
        session.is_gold = None
        session.is_silver = None
        session.is_diamond = None
        session.max_price = None
        session.min_price = None
        session.current_category = None
        session.current_products = []
        session.base_products = []
        session.selected_product = None
        session.current_page = 1
        session.category_distribution = None
        session.target_categories = []

        db_categories = await self.product_service.get_categories()
        # Sort to keep presentation consistent
        sorted_categories = sorted(list(set(db_categories)))
        
        category_emojis = {
            "rings": "💍",
            "ring": "💍",
            "necklaces": "📿",
            "necklace": "📿",
            "pendants": "✨",
            "pendant": "✨",
            "earrings": "👂",
            "earring": "👂",
            "bracelets": "🪬",
            "bracelet": "🪬",
            "bangles": "⭕",
            "bangle": "⭕",
            "chains": "⛓️",
            "chain": "⛓️",
            "bridal collection": "👑",
            "bridal": "👑"
        }
        
        cat_lines = []
        for cat in sorted_categories:
            emoji = category_emojis.get(cat.lower(), "💎")
            cat_lines.append(f"{emoji} {cat}")
            
        categories_str = "\n\n".join(cat_lines)
        
        response = (
            "💎 SSJewellery Categories\n\n"
            "We currently offer the following jewellery categories:\n\n"
            f"{categories_str}\n\n"
            "✨ You can also search naturally. For example:\n\n"
            "• Show me gold rings\n\n"
            "• Diamond necklaces under ₹50,000\n\n"
            "• Bridal jewellery\n\n"
            "• Daily wear earrings\n\n"
            "Simply reply with any category name to explore products."
        )
        
        # When displaying categories, set the flow and step to wait for user's category choice
        session.current_flow = "product_search"
        session.current_step = "waiting_category"
        session.update_access()
        return response

    async def _handle_product_search(self, session: UserSession, category: Optional[str], message_text: str) -> str:
        # Clear previous search filters on initiating a new search
        session.is_gold = None
        session.is_silver = None
        session.is_diamond = None
        session.max_price = None
        session.min_price = None
        session.current_category = None
        session.current_products = []
        session.base_products = []
        session.selected_product = None
        session.current_page = 1
        session.category_distribution = None
        session.target_categories = []

        db_categories = await self.product_service.get_categories()

        # Try to match categories
        target_categories = []
        if category:
            target_categories = self.product_service.match_categories(category, db_categories)
        if not target_categories:
            target_categories = self.product_service.match_categories(message_text, db_categories)

        print(f"Detected Intent: PRODUCT_SEARCH")
        print(f"Detected Category: {category or ', '.join(target_categories)}")

        if not target_categories:
            # No categories matched, start product search flow
            session.current_flow = "product_search"
            session.current_step = "waiting_category"
            session.current_intent = "PRODUCT_SEARCH"
            session.update_access()
            return "Which category are you looking for?"

        try:
            # Query products for each category and merge them
            base_list = []
            
            # Extract price limit from query if present
            query_lower = message_text.lower()
            price_limit: Optional[float] = None
            price_match = re.search(r'(?:under|below|less than|max|maximum)\s*(?:rs\.?|inr|₹)?\s*([\d,]+)', query_lower)
            if price_match:
                try:
                    price_str = price_match.group(1).replace(',', '')
                    price_limit = float(price_str)
                except ValueError:
                    pass

            for cat in target_categories:
                # Query database for all products of this category (limit 100)
                dict_products = await self.product_service.repository.search_products(
                    query_text=message_text,
                    category_name=cat,
                    max_price=price_limit,
                    limit=100
                )
                for p_dict in dict_products:
                    # Set the product's own category URL as the website_url
                    p_dict["website_url"] = URLBuilder.get_category_url(p_dict["category"])
                    base_list.append(p_dict)

            # If no products, try closest matching category
            if not base_list and len(target_categories) == 1:
                closest_cat = self.product_service.find_closest_category(message_text, db_categories)
                if closest_cat and closest_cat not in target_categories:
                    dict_products = await self.product_service.repository.search_products(
                        query_text=message_text,
                        category_name=closest_cat,
                        max_price=price_limit,
                        limit=100
                    )
                    if dict_products:
                        target_categories = [closest_cat]
                        for p_dict in dict_products:
                            p_dict["website_url"] = URLBuilder.get_category_url(p_dict["category"])
                            base_list.append(p_dict)

            # Fallback: search without category constraint
            if not base_list:
                dict_products = await self.product_service.repository.search_products(
                    query_text=message_text,
                    category_name=None,
                    max_price=price_limit,
                    limit=100
                )
                if dict_products:
                    target_categories = []
                    for p_dict in dict_products:
                        p_dict["website_url"] = URLBuilder.get_category_url(p_dict["category"])
                        base_list.append(p_dict)

            print(f"Number of Products Returned: {len(base_list)}")

            if not base_list:
                # Keep in product search flow so they can choose again
                session.current_flow = "product_search"
                session.current_step = "waiting_category"
                session.current_intent = "PRODUCT_SEARCH"
                session.update_access()
                return format_no_products_found()

            # Store result in session
            session.current_category = ", ".join(target_categories)
            session.base_products = base_list
            session.target_categories = target_categories

            # Apply filters if present in message text
            self._parse_and_update_filters(session, message_text)
            filtered = self._apply_filters_to_list(session.base_products, session)

            session.current_products = filtered
            session.current_page = 1
            
            # Fetch the first page products using intelligent distribution
            first_page_products = self._get_products_for_page(filtered, target_categories, 1, session)

            if first_page_products:
                session.selected_product = first_page_products[0]
            session.update_access()

            if not first_page_products:
                session.reset()
                return "No matching products found with the applied filters."

            from app.schemas import Product
            products_to_send = [Product(**p) for p in first_page_products]

            captions = await self.image_response_builder.send_product_responses(
                recipient_phone=session.phone_number,
                products=products_to_send
            )

            print(f"Formatted Response: {captions}")

            is_corrected = session.data.get("is_corrected", False)
            display_query = session.data.get("display_query", "")

            is_test = session.phone_number in ["12345", "919999999999", "919829276750"] or len(session.phone_number) < 7
            if is_corrected and display_query:
                correction_text = f"Showing results for {display_query}."
                if is_test:
                    response = f"{correction_text}\n\n" + "\n\n---\n\n".join(captions)
                else:
                    await self.image_response_builder.whatsapp_client.send_whatsapp_message(
                        recipient_phone=session.phone_number,
                        message_text=correction_text
                    )
                    response = ""
            else:
                if is_test:
                    response = f"✨ *Here are the matching products I found for \"{message_text}\":*\n\n" + "\n\n---\n\n".join(captions)
                else:
                    response = ""

            print(f"WhatsApp Response: {repr(response)}")

            session.reset() # Reset flow/step but keep products in session for pagination/filtering
            return response

        except DatabaseConnectionError:
            session.reset()
            return "Unable to retrieve products at the moment."

    async def handle_message(self, sender_phone: str, message_text: str, sender_name: str) -> str:
        """
        Handles incoming message based on session state and detected intent.
        """
        # 1. Retrieve or initialize the user's session
        session: UserSession = self.session_manager.get_session(sender_phone)
        
        # Apply spelling correction (Feature 1)
        from app.services.spell_checker import process_spelling_correction
        message_corrected, display_query, is_corrected = process_spelling_correction(message_text)
        
        session.data["is_corrected"] = is_corrected
        session.data["display_query"] = display_query
        
        message_clean = message_corrected.strip()
        is_new_session = len(session.messages) == 0

        # Add user message to history
        session.add_message("user", message_clean)

        # 2. Check for specific context resolution (Order status follow-up)
        if session.current_order:
            message_lower = message_clean.lower()
            if any(w in message_lower for w in ["arrive", "delivery", "when is it", "when will", "when to"]):
                order_obj = Order(**session.current_order)
                order_obj.tracking_url = URLBuilder.get_order_url(order_obj.id)
                response = format_order_status(order_obj)
                session.add_message("assistant", response)
                return response

        # 3. Check for specific context resolution (Product select, view link, pagination, or filters)
        if session.base_products or session.current_products:
            message_lower = message_clean.lower()

            # A. Select index: "show image of the first one", "first one", "1st one", etc.
            is_index_request = any(w in message_lower for w in ["first", "1st", "second", "2nd", "third", "3rd", "one", "two", "three"])
            is_visual_request = any(w in message_lower for w in ["image", "photo", "pic", "picture", "show"])
            
            if is_index_request and is_visual_request:
                idx = -1
                if any(w in message_lower for w in ["third", "3rd", "three"]):
                    idx = 2
                elif any(w in message_lower for w in ["second", "2nd", "two"]):
                    idx = 1
                elif any(w in message_lower for w in ["first", "1st", "one"]):
                    idx = 0
                
                # Try to use current filtered products first
                products_list = session.current_products or session.base_products
                if 0 <= idx < len(products_list):
                    product_dict = products_list[idx]
                    session.selected_product = product_dict
                    session.update_access()
                    
                    from app.schemas import Product
                    product_obj = Product(**product_dict)
                    
                    captions = await self.image_response_builder.send_product_responses(
                        recipient_phone=session.phone_number,
                        products=[product_obj]
                    )
                    
                    is_test = session.phone_number in ["12345", "919999999999", "919829276750"] or len(session.phone_number) < 7
                    if is_test:
                        response = captions[0] if captions else ""
                    else:
                        response = ""
                    
                    session.add_message("assistant", response or f"Sent image for {product_obj.name}")
                    return response

            # B. Open product link: "open that product", "open product", "view product", "view that", "link", "url", "website"
            if any(w in message_lower for w in ["open", "view", "link", "url", "website"]):
                url = URLBuilder.get_category_url(session.current_category or "")
                response = f"🔗 _View Product:_ {url}"
                session.add_message("assistant", response)
                return response

            # C. Pagination: "More", "Next", etc.
            if message_lower in ["more", "show more", "next", "more products", "next products"]:
                page = session.current_page + 1
                
                target_categories = session.target_categories
                if not target_categories and session.current_category:
                    target_categories = [c.strip() for c in session.current_category.split(",") if c.strip()]
                if not target_categories:
                    target_categories = []

                filtered = self._apply_filters_to_list(session.base_products, session)
                next_products_dicts = self._get_products_for_page(filtered, target_categories, page, session)
                
                if next_products_dicts:
                    session.current_page = page
                    session.current_products = filtered
                    session.selected_product = next_products_dicts[0]
                    session.update_access()
                    
                    from app.schemas import Product
                    next_products_objs = [Product(**p) for p in next_products_dicts]
                    
                    captions = await self.image_response_builder.send_product_responses(
                        recipient_phone=session.phone_number,
                        products=next_products_objs
                    )
                    
                    is_test = session.phone_number in ["12345", "919999999999", "919829276750"] or len(session.phone_number) < 7
                    if is_test:
                        response = f"✨ *Here are the next products I found:* \n\n" + "\n\n---\n\n".join(captions)
                    else:
                        response = ""
                        
                    session.add_message("assistant", response or "Sent next products.")
                    return response
                else:
                    response = "You have reached the end of the product list. There are no more products matching your search."
                    session.add_message("assistant", response)
                    return response

            # D. In-memory Filter request (e.g., "Only gold", "Under Rs. 20,000")
            is_filter_request = any(w in message_lower for w in ["gold", "silver", "diamond", "under", "below", "price", "only", "rs.", "inr", "₹"])
            db_categories = await self.product_service.get_categories()
            category_in_msg = self.product_service.extract_category_from_text(message_clean)
            if category_in_msg:
                if any(w in message_lower for w in ["show", "find", "search", "get", "want", "need"]):
                    is_filter_request = False
                elif category_in_msg != session.current_category:
                    is_filter_request = False

            if is_filter_request:
                self._parse_and_update_filters(session, message_clean)
                filtered = self._apply_filters_to_list(session.base_products, session)
                
                session.current_products = filtered
                session.current_page = 1
                session.category_distribution = None # Recalculate distribution based on filtered counts
                
                target_categories = session.target_categories
                if not target_categories and session.current_category:
                    target_categories = [c.strip() for c in session.current_category.split(",") if c.strip()]
                if not target_categories:
                    target_categories = []

                first_page_products = self._get_products_for_page(filtered, target_categories, 1, session)
                
                session.selected_product = first_page_products[0] if first_page_products else None
                session.update_access()
                
                if not first_page_products:
                    response = "No matching products found with the applied filters."
                    session.add_message("assistant", response)
                    return response
                
                from app.schemas import Product
                products_to_send = [Product(**p) for p in first_page_products]
                
                captions = await self.image_response_builder.send_product_responses(
                    recipient_phone=session.phone_number,
                    products=products_to_send
                )
                
                is_test = session.phone_number in ["12345", "919999999999", "919829276750"] or len(session.phone_number) < 7
                if is_test:
                    response = f"✨ *Here are the matching products I found for \"{message_clean}\":*\n\n" + "\n\n---\n\n".join(captions)
                else:
                    response = ""
                
                session.add_message("assistant", response or "Sent filtered products.")
                return response

        # 4. Pre-detect intent with history and structured context
        analysis: IntentAnalysis = await self.intent_service.detect_intent(
            message_clean, 
            history=session.messages, 
            context=session.get_structured_context()
        )
        
        # Local keyword/category extraction to force PRODUCT_SEARCH intent and avoid AI rate limits
        db_categories = await self.product_service.get_categories()
        extracted_cats = self.product_service.match_categories(message_clean, db_categories)
        if extracted_cats and analysis.intent != "CATEGORY_LIST":
            analysis.intent = "PRODUCT_SEARCH"
            analysis.category = ", ".join(extracted_cats)

        # Force intent to GREETING if message matches a greeting trigger or is detected as GREETING
        message_normalized = re.sub(r'[^\w\s]', '', message_clean).strip().lower()
        is_greeting_trigger = message_normalized in {
            "hi", "hello", "hey", "hii", "start", "good morning", "good evening", "namaste", "greetings"
        }
        if is_greeting_trigger or analysis.intent == "GREETING":
            analysis.intent = "GREETING"

        session.current_intent = analysis.intent
        session.update_access()

        # Force intent to SHOPPING_ASSISTANCE if they are actively in the shopping assistance budget step
        if session.current_flow == "shopping_assistance" and session.current_step == "waiting_budget":
            message_digits = re.sub(r'[^\d]', '', message_clean)
            if message_digits and len(message_digits) >= 3:
                analysis.intent = "SHOPPING_ASSISTANCE"

        # 5. Check for explicit context switch
        should_switch = False
        if session.current_flow:
            # We switch to ORDER_TRACKING, SUPPORT, or CATEGORY_LIST if it's different from the current flow
            if analysis.intent in ["ORDER_TRACKING", "SUPPORT", "CATEGORY_LIST", "SHOPPING_ASSISTANCE", "SURPRISE_ME"] and session.current_flow != self._get_flow_for_intent(analysis.intent):
                should_switch = True
            
            # We only switch to PRODUCT_SEARCH from support_ticket/order_tracking if they explicitly ask to find/show products
            elif analysis.intent == "PRODUCT_SEARCH" and session.current_flow != "product_search":
                is_explicit = any(w in message_clean.lower() for w in ["show", "find", "buy", "search", "looking for", "want", "get"])
                if is_explicit:
                    should_switch = True
                    
            elif analysis.intent == "PRODUCT_SEARCH" and session.current_flow == "product_search":
                current_cat = session.current_category
                if analysis.category and current_cat and analysis.category.lower() != current_cat.lower():
                    should_switch = True
                    
            if message_clean.lower() in ["cancel", "reset", "exit", "stop"]:
                should_switch = True
 
        if should_switch:
            print(f"Context switch detected for {sender_phone}. Resetting active flow {session.current_flow}.")
            session.reset()
 
        # 6. Priority 1: Active Conversation Context
        response = None
        if session.current_flow:
            response = await self._process_active_flow(session, message_clean, sender_name)
 
        # 7. Route other priorities
        if response is None:
            intent = analysis.intent
            entity = analysis.extracted_entity
            category = analysis.category

            if intent == "PRODUCT_SEARCH":
                response = await self._handle_product_search(session, category, message_clean)

            elif intent == "CATEGORY_LIST":
                response = await self._handle_category_list(session)

            elif intent == "ORDER_TRACKING":
                if session.current_order and not entity:
                    order_obj = Order(**session.current_order)
                    order_obj.tracking_url = URLBuilder.get_order_url(order_obj.id)
                    response = format_order_status(order_obj)
                elif entity:
                    order = await self.order_service.get_order_status(entity)
                    if order:
                        order.tracking_url = URLBuilder.get_order_url(order.id)
                        session.current_order = order.model_dump() if hasattr(order, 'model_dump') else order.dict()
                        session.reset()
                        response = format_order_status(order)
                    else:
                        session.reset()
                        response = format_order_not_found(entity, sender_name)
                else:
                    session.current_flow = "order_tracking"
                    session.current_step = "waiting_order_id"
                    session.update_access()
                    response = format_ask_order_id(sender_name)

            elif intent == "SUPPORT":
                if entity:
                    session.current_flow = "support_ticket"
                    session.current_step = "waiting_email"
                    session.data["issue"] = entity
                    session.update_access()
                    response = format_ask_support_email()
                else:
                    session.current_flow = "support_ticket"
                    session.current_step = "waiting_issue"
                    session.update_access()
                    response = format_ask_support_issue()

            elif intent == "SHOPPING_ASSISTANCE":
                response = await self.handle_shopping_flow(session, message_clean)

            elif intent == "SURPRISE_ME":
                response = await self.handle_surprise_me(session)

            elif intent == "GREETING" and is_new_session:
                session.reset()
                welcome_caption = format_greeting()
                logo_url = settings.WELCOME_LOGO_URL.strip() if settings.WELCOME_LOGO_URL else ""
                if logo_url:
                    try:
                        await self.image_response_builder.whatsapp_client.send_image_message(
                            recipient_phone=session.phone_number,
                            image_url=logo_url,
                            caption=welcome_caption
                        )
                    except Exception as logo_exc:
                        print(f"Failed to send brand logo image: {logo_exc}.")
                    session.add_message("assistant", welcome_caption)
                    response = ""
                else:
                    response = welcome_caption

            else:
                # General Gemini Chat or active session fallback (Priority 6)
                session.reset()
                try:
                    response = await self.gemini_client.generate_ai_response(
                        message_clean, 
                        sender_name, 
                        history=session.messages,
                        context=session.get_structured_context()
                    )
                except Exception as exc:
                    print(f"Error calling Gemini Client: {exc}. Using friendly active fallback.")
                    if is_new_session:
                        response = f"Hello {sender_name}! Welcome to SSJewellery. How can I assist you today?"
                    else:
                        response = "I'm here to help you with product search, order tracking, and support. What would you like to do next?"

        if response:
            session.add_message("assistant", response)
 
        return response

    def _get_flow_for_intent(self, intent: str) -> str:
        mapping = {
            "ORDER_TRACKING": "order_tracking",
            "SUPPORT": "support_ticket",
            "PRODUCT_SEARCH": "product_search",
            "CATEGORY_LIST": "category_list",
            "SHOPPING_ASSISTANCE": "shopping_assistance",
            "SURPRISE_ME": "shopping_assistance"
        }
        return mapping.get(intent, "")
 
    def _parse_and_update_filters(self, session: UserSession, text: str) -> None:
        text_lower = text.lower()
        
        # Parse metals and update session
        if "gold" in text_lower:
            session.is_gold = True
            session.is_silver = False
            session.is_diamond = False
        if "silver" in text_lower:
            session.is_silver = True
            session.is_gold = False
            session.is_diamond = False
        if "diamond" in text_lower:
            session.is_diamond = True
            session.is_gold = False
            session.is_silver = False
            
        # Parse price and update session
        price_match = re.search(r'(?:under|below|less than|max|maximum|budget|rs\.?|inr|₹)?\s*([\d,]+)', text_lower)
        if price_match:
            try:
                price_str = price_match.group(1).replace(',', '')
                price_val = float(price_str)
                # Keep budget if it is a reasonable search number
                if price_val > 100:
                    session.max_price = price_val
                    session.min_price = None
            except ValueError:
                pass
 
    def _apply_filters_to_list(self, products: List[dict], session: UserSession) -> List[dict]:
        filtered = []
        for p in products:
            price = p.get("price", 0.0)
            if session.max_price is not None and price > session.max_price:
                continue
            if session.min_price is not None and price < session.min_price:
                continue
                
            name_desc = (p.get("name", "") + " " + p.get("description", "")).lower()
            if session.is_gold and "gold" not in name_desc:
                continue
            if session.is_silver and "silver" not in name_desc:
                continue
            if session.is_diamond and "diamond" not in name_desc:
                continue
                
            filtered.append(p)
        return filtered
 
    async def _process_active_flow(self, session: UserSession, message_text: str, sender_name: str) -> Optional[str]:
        """
        Process the message if there's an active conversation flow.
        Returns the response string if handled, or None if the message was not handled.
        """
        text_lower = message_text.lower()
        if text_lower in ["cancel", "reset", "exit", "stop"]:
            session.reset()
            return None
 
        if session.current_flow == "order_tracking":
            if session.current_step == "waiting_order_id":
                order = await self.order_service.get_order_status(message_text)
                if order:
                    order.tracking_url = URLBuilder.get_order_url(order.id)
                    session.current_order = order.model_dump() if hasattr(order, 'model_dump') else order.dict()
                    response = format_order_status(order)
                    session.reset()
                    return response
                else:
                    response = format_order_not_found(message_text, sender_name)
                    session.reset()
                    return response
 
        elif session.current_flow == "support_ticket":
            if session.current_step == "waiting_issue":
                session.data["issue"] = message_text
                session.current_step = "waiting_email"
                session.update_access()
                return format_ask_support_email()
 
            elif session.current_step == "waiting_email":
                if not re.match(EMAIL_REGEX, message_text):
                    session.update_access()
                    return format_invalid_email()
                
                issue = session.data.get("issue", "General Support")
                ticket = await self.support_service.create_ticket(issue, message_text)
                response = format_support_ticket_created(ticket)
                session.reset()
                return response
 
        elif session.current_flow == "product_search":
            if session.current_step == "waiting_category" or session.current_step == "waiting_product_type":
                # Clear previous search filters on initiating a new search
                session.is_gold = None
                session.is_silver = None
                session.is_diamond = None
                session.max_price = None
                session.min_price = None
 
                response = await self._handle_product_search(session, None, message_text)
                return response

        elif session.current_flow == "shopping_assistance":
            response = await self.handle_shopping_flow(session, message_text)
            return response
 
        return None

    async def handle_surprise_me(self, session: UserSession) -> str:
        # Query database for popular products (no query, no category, max limit)
        dict_products = await self.product_service.repository.search_products(
            query_text=None,
            category_name=None,
            max_price=None,
            limit=3
        )
        for p_dict in dict_products:
            p_dict["website_url"] = URLBuilder.get_category_url(p_dict["category"])
            
        session.base_products = dict_products
        session.current_products = dict_products
        session.current_page = 1
        session.target_categories = []
        session.update_access()
        
        from app.schemas import Product
        products_to_send = [Product(**p) for p in dict_products]
        
        captions = await self.image_response_builder.send_product_responses(
            recipient_phone=session.phone_number,
            products=products_to_send
        )
        
        is_test = session.phone_number in ["12345", "919999999999", "919829276750"] or len(session.phone_number) < 7
        if is_test:
            response = f"✨ *Here are the recommended products:* \n\n" + "\n\n---\n\n".join(captions)
        else:
            response = ""
            
        session.reset()
        return response

    async def _handle_shopping_search_results(self, session: UserSession) -> str:
        db_categories = await self.product_service.get_categories()
        target_categories = self.product_service.match_categories(session.current_category, db_categories)
        if not target_categories:
            target_categories = [session.current_category]
            
        base_list = []
        for cat in target_categories:
            query_text = ""
            if session.is_gold:
                query_text = "gold"
            elif session.is_silver:
                query_text = "silver"
            elif session.is_diamond:
                query_text = "diamond"
                
            dict_products = await self.product_service.repository.search_products(
                query_text=query_text,
                category_name=cat,
                max_price=session.max_price,
                limit=100
            )
            for p_dict in dict_products:
                p_dict["website_url"] = URLBuilder.get_category_url(p_dict["category"])
                base_list.append(p_dict)
                
        filtered = self._apply_filters_to_list(base_list, session)
        
        session.base_products = base_list
        session.current_products = filtered
        session.current_page = 1
        session.target_categories = target_categories
        session.update_access()
        
        if not filtered:
            session.reset()
            return "No matching products found with the applied filters."
            
        first_page_products = self._get_products_for_page(filtered, target_categories, 1, session)
        if first_page_products:
            session.selected_product = first_page_products[0]
            
        from app.schemas import Product
        products_to_send = [Product(**p) for p in first_page_products]
        
        captions = await self.image_response_builder.send_product_responses(
            recipient_phone=session.phone_number,
            products=products_to_send
        )
        
        is_test = session.phone_number in ["12345", "919999999999", "919829276750"] or len(session.phone_number) < 7
        if is_test:
            response = f"✨ *Here are the matching products I found:* \n\n" + "\n\n---\n\n".join(captions)
        else:
            response = ""
            
        session.reset()
        return response

    async def handle_shopping_flow(self, session: UserSession, message_text: str) -> str:
        message_lower = message_text.lower().strip()
        
        # 0. Check for "don't know what to buy" / "dont know what to buy"
        if "don't know what to buy" in message_lower or "dont know what to buy" in message_lower or "help me choose" in message_lower:
            session.current_flow = "shopping_assistance"
            session.current_step = "waiting_guided_details"
            session.update_access()
            return (
                "No problem 😊\n\n"
                "I'll help you.\n\n"
                "Please tell me:\n"
                "• Occasion\n"
                "• Budget\n"
                "• Preferred jewellery"
            )

        # 1. Extract budget if present in message
        price_match = re.search(r'(?:under|below|less than|max|maximum|budget|rs\.?|inr|₹)?\s*([\d,]+)', message_lower)
        if price_match:
            try:
                price_str = price_match.group(1).replace(',', '')
                price_val = float(price_str)
                if price_val > 100:
                    session.max_price = price_val
                    session.data["budget"] = price_val
            except ValueError:
                pass
                
        # 2. Extract metal preferences
        if "gold" in message_lower:
            session.is_gold = True
        if "silver" in message_lower:
            session.is_silver = True
        if "diamond" in message_lower:
            session.is_diamond = True
            
        # 3. Extract category if present
        db_categories = await self.product_service.get_categories()
        matched_cats = self.product_service.match_categories(message_text, db_categories)
        if matched_cats:
            session.current_category = matched_cats[0]
            session.target_categories = matched_cats
            
        # 4. Extract occasion / recipient
        occasions_map = {
            "wedding": "Wedding",
            "engagement": "Engagement",
            "gift": "Gift",
            "office": "Office Wear",
            "daily": "Daily Wear",
            "party": "Party Wear",
            "luxury": "Luxury",
            "minimal": "Minimal",
            "traditional": "Traditional",
            "modern": "Modern",
            "bridal": "Bridal",
            "festival": "Festival",
            "anniversary": "Anniversary",
            "birthday": "Birthday",
            "proposal": "Proposal"
        }
        for kw, occ in occasions_map.items():
            if kw in message_lower:
                session.data["occasion"] = occ
                
        recipients_list = ["mother", "sister", "wife", "friend", "bride"]
        for r in recipients_list:
            if r in message_lower:
                session.data["recipient"] = r.capitalize()

        # 5. Let's see if we have enough info to show products (both category and budget selected)
        budget = session.max_price
        if session.current_category and budget:
            return await self._handle_shopping_search_results(session)

        # 6. Guide them based on what we have so far
        occasion = session.data.get("occasion")
        recipient = session.data.get("recipient")
        
        session.current_flow = "shopping_assistance"
        
        if not occasion:
            session.current_step = "waiting_occasion"
            session.update_access()
            return (
                "Sure 😊\n\n"
                "Who is it for?\n"
                "• Wedding\n"
                "• Engagement\n"
                "• Gift\n"
                "• Office Wear\n"
                "• Daily Wear\n"
                "• Party Wear"
            )
            
        if occasion == "Gift" and not recipient:
            session.current_step = "waiting_recipient"
            session.update_access()
            return (
                "Wonderful 🎁\n\n"
                "Who is the gift for?\n"
                "• Mother\n"
                "• Sister\n"
                "• Wife\n"
                "• Friend\n"
                "• Bride"
            )
            
        if occasion == "Wedding" and not session.current_category:
            session.current_step = "waiting_category"
            session.update_access()
            return (
                "Great choice.\n\n"
                "Would you like:\n"
                "• Rings\n"
                "• Necklaces\n"
                "• Bridal Collection\n"
                "• Earrings"
            )
            
        if not session.current_category:
            session.current_step = "waiting_category"
            session.update_access()
            return (
                "Great choice.\n\n"
                "Would you like:\n"
                "• Rings\n"
                "• Necklaces\n"
                "• Bridal Collection\n"
                "• Earrings"
            )

        if not budget:
            session.current_step = "waiting_budget"
            session.update_access()
            budget_options = (
                "What's your approximate budget?\n"
                "• Under ₹20,000\n"
                "• ₹20,000–₹50,000\n"
                "• Above ₹50,000"
            )
            if recipient:
                return budget_options
            else:
                return f"Great choice. {budget_options}"
 
    async def _handle_new_intent(self, session: UserSession, analysis: IntentAnalysis, message_text: str, sender_name: str) -> str:
        # Legacy method stub just in case it is called anywhere else
        return ""

