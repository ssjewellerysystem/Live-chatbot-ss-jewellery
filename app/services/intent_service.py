import re
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.config import settings
from app.exceptions import GeminiAPIError

from typing import Optional, List, Dict, Any

class IntentAnalysis(BaseModel):
    intent: str = Field(description="Must be one of: GREETING, PRODUCT_SEARCH, ORDER_TRACKING, SUPPORT, GENERAL_CHAT, CATEGORY_LIST, SHOPPING_ASSISTANCE, SURPRISE_ME")
    extracted_entity: str = Field(description="Extracted search term, order ID, or support issue summary. Leave empty if none.")
    category: Optional[str] = Field(
        default=None,
        description="Only for PRODUCT_SEARCH, detect the requested category from these exact choices: Ring, Earrings, Necklace, Bracelet, Bangles, Chain, Pendant, Bridal Collection. Leave empty if no specific category is requested."
    )

class IntentService:
    """
    Service to detect user intent and extract query parameters using Gemini structured outputs.
    """
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def detect_intent(
        self, 
        message_text: str, 
        history: Optional[List[Dict[str, str]]] = None, 
        context: Optional[Dict[str, Any]] = None
    ) -> IntentAnalysis:
        """
        Analyzes the user's message using Gemini to determine the business intent
        and extract the relevant target entity.
        """
        text_lower = message_text.lower().strip()

        # Prioritize CATEGORY_LIST routing before LLM
        category_list_phrases = [
            "show me all categories", "show all category", "show all categories", 
            "available categories", "which categories are available", 
            "what categories do you have", "what kind of jewellery do you have", 
            "what kind of jewelry do you have", "which type of jewellery is available", 
            "which type of jewelry is available", "show category list", 
            "list all categories", "jewellery categories", "jewelry categories", 
            "product categories", "browse categories", "what can i buy", 
            "what products are available", "all categories", "list categories", 
            "categories list"
        ]
        clean_text_for_match = re.sub(r'[?.,!]', '', text_lower).strip()
        if any(p in clean_text_for_match for p in category_list_phrases):
            return IntentAnalysis(intent="CATEGORY_LIST", extracted_entity="")

        # Prioritize ORDER_TRACKING routing before Greeting or Default intents
        is_tracking = False

        # Match specific Order ID patterns (e.g., SJ10245, BB-792984, TRK12345) or general numeric IDs (5+ digits)
        has_order_pattern = re.search(r'\b(?:sj|bb|trk)\s*-?\s*\d+\b', text_lower)
        has_general_digits = re.search(r'\b\d{5,}\b', text_lower)
        is_price_value = re.search(r'(?:under|below|less than|max|maximum|budget|rs\.?|inr|₹|\babove\b|\bmore than\b|\bover\b)\s*₹?\s*\d+', text_lower)
        if has_order_pattern or (has_general_digits and not is_price_value):
            is_tracking = True

        # Match exact order tracking phrases or keywords
        tracking_phrases = [
            "track my order", "order status", "check my order", "where is my order",
            "order tracking", "track order", "track order status", "check order status",
            "my order", "delivery status", "shipment status", "order update",
            "track package", "where is my package", "i want to track my order",
            "check my shipment", "order details", "my delivery", "track shipment",
            "tracking status", "shipment status", "package status"
        ]
        if any(p in text_lower for p in tracking_phrases):
            is_tracking = True

        # Check generic combinations (e.g. "where is my package")
        if "where is" in text_lower and any(w in text_lower for w in ["package", "shipment", "delivery", "order"]):
            is_tracking = True

        if is_tracking:
            order_id = ""
            order_match = re.search(r'\b(?:sj|bb|trk)\s*-?\s*\d+\b', text_lower)
            if not order_match and not is_price_value:
                order_match = re.search(r'\b\d{5,}\b', text_lower)
            if order_match:
                order_id = order_match.group().replace(" ", "").upper()
            cleaned_entity = self._clean_extracted_entity("ORDER_TRACKING", order_id)
            return IntentAnalysis(intent="ORDER_TRACKING", extracted_entity=cleaned_entity)

        current_category = None
        if context:
            current_category = context.get("Current Product Category") or context.get("current_category")

        history_str = ""
        if history:
            for msg in history[:-1]:  # exclude the latest user message which is message_text
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['text']}\n"

        context_str = json.dumps(context or {}, indent=2)

        prompt = (
            f"Structured Conversation Context:\n"
            f"{context_str}\n\n"
            f"Recent Conversation History:\n"
            f"{history_str or '(No previous history)'}\n\n"
            f"Latest User Message:\n"
            f"\"\"\"{message_text}\"\"\"\n\n"
            f"Analyze the Latest User Message in the context of the structured conversation context and recent conversation history.\n\n"
            f"Classify the message and extract target entities:\n"
            f"1. intent: Must be one of: GREETING, PRODUCT_SEARCH, ORDER_TRACKING, SUPPORT, GENERAL_CHAT, CATEGORY_LIST, SHOPPING_ASSISTANCE, SURPRISE_ME.\n"
            f"   - GREETING: If the message is a greeting like 'Hi', 'Hello', 'Hey', 'Good Morning', 'Good Evening', etc.\n"
            f"   - CATEGORY_LIST: If the user explicitly asks to show, list, view, or browse available jewellery categories, product categories, or what jewellery/products/categories they can buy or are available. E.g. 'Show me all categories', 'what categories do you have?', 'available categories', 'what kind of jewellery do you have?', etc.\n"
            f"   - PRODUCT_SEARCH: If the user is searching for jewelry, rings, necklaces, earrings, bangles, bridal collection, bracelets, chain, pendants, etc. Or if the message is a follow-up filter to a previous search (e.g. 'only gold', 'under 20000', 'show the first one').\n"
            f"   - ORDER_TRACKING: If the user is asking to track their order, status of their order, e.g. 'Track Order', 'Where is my order', or provides an order ID.\n"
            f"   - SUPPORT: If the user needs help, customer support, has a complaint, wants to report an issue, etc., e.g. 'Need Help', 'Support', 'Complaint'.\n"
            f"   - SHOPPING_ASSISTANCE: If the user needs help choosing jewellery, wants shopping advice, says 'I need jewellery', 'I want to buy a gift', 'I don't know what to buy', or specifies occasions/recipients like 'Wedding', 'For my wife' without a specific search query.\n"
            f"   - SURPRISE_ME: If the user says 'Surprise me' or asks for general recommendations.\n"
            f"   - GENERAL_CHAT: If the message is a general query, small talk, or doesn't fit any of the above.\n"
            f"2. extracted_entity: Extracted search term, order ID, or support issue summary.\n"
            f"3. category: Only for PRODUCT_SEARCH, determine the specific category of interest from this list (or the current category from history if the user is filtering results):\n"
            f"   - Ring (if user wants rings, rose gold band, solitaire ring, etc.)\n"
            f"   - Earrings (if user wants earrings, jhumkas, studs, etc.)\n"
            f"   - Necklace (if user wants necklaces, chokers, etc.)\n"
            f"   - Bracelet (if user wants bracelets, bands, etc.)\n"
            f"   - Bangles (if user wants bangles, kadas, etc.)\n"
            f"   - Chain (if user wants chains, etc.)\n"
            f"   - Pendant (if user wants pendants, etc.)\n"
            f"   - Bridal Collection (if user wants bridal collection, kundan bridal set, etc.)\n"
            f"   Leave 'category' empty if no specific category from the list above is mentioned."
        )

        try:
            # Using structured JSON output to guarantee Pydantic schema compliance
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IntentAnalysis,
                    temperature=0.1  # Low temperature for deterministic classification
                )
            )

            parsed = None
            if hasattr(response, 'parsed') and response.parsed:
                parsed = response.parsed
            else:
                raw_text = response.text
                if not raw_text:
                    raise GeminiAPIError("Received empty intent analysis response from Gemini.")
                data = json.loads(raw_text.strip())
                parsed = IntentAnalysis(**data)

            # Map SUPPORT_REQUEST to SUPPORT for backwards-compatibility support
            if parsed.intent == "SUPPORT_REQUEST":
                parsed.intent = "SUPPORT"

            # Post-process to remove generic intent triggers from extracted_entity
            parsed.extracted_entity = self._clean_extracted_entity(parsed.intent, parsed.extracted_entity)
            return parsed

        except Exception as exc:
            # Fallback to local rule-based parsing on Gemini API failure/quota limit
            print(f"Error in IntentService: {str(exc)}. Activating rule-based fallback routing.")
            return self._rule_based_fallback(message_text, current_category)

    def _clean_extracted_entity(self, intent: str, entity: str) -> str:
        """
        Cleans up extracted entities to remove generic trigger phrases that should not be treated as actual query values.
        """
        entity_clean = entity.strip()
        entity_lower = entity_clean.lower()
        
        if intent == "SUPPORT":
            generic_support_triggers = {
                "support", "need support", "help", "need help", "complaint", "report complaint",
                "create ticket", "create a support ticket", "ticket", "issue", "get support",
                "customer service", "get help", "contact support", "customer support", "raise ticket"
            }
            if entity_lower in generic_support_triggers or len(entity_lower) < 4:
                return ""
                
        elif intent == "ORDER_TRACKING":
            generic_order_triggers = {
                "track order", "track my order", "order status", "track", "status",
                "where is my order", "order tracking", "my order", "tracking status"
            }
            if entity_lower in generic_order_triggers or len(entity_lower) < 4:
                return ""

        return entity_clean

    def _rule_based_fallback(self, text: str, current_category: Optional[str] = None) -> IntentAnalysis:
        """
        Regex and keyword fallback to identify intent when Gemini API hits quota limits.
        """
        text_lower = text.lower().strip()
        
        # 0. Detect Category List intent
        category_list_phrases = [
            "show me all categories", "show all category", "show all categories", 
            "available categories", "which categories are available", 
            "what categories do you have", "what kind of jewellery do you have", 
            "what kind of jewelry do you have", "which type of jewellery is available", 
            "which type of jewelry is available", "show category list", 
            "list all categories", "jewellery categories", "jewelry categories", 
            "product categories", "browse categories", "what can i buy", 
            "what products are available", "all categories", "list categories", 
            "categories list"
        ]
        clean_text_for_match = re.sub(r'[?.,!]', '', text_lower).strip()
        if any(p in clean_text_for_match for p in category_list_phrases):
            return IntentAnalysis(intent="CATEGORY_LIST", extracted_entity="")

        # 1. Detect Greeting intent
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "hii", "heyy"]
        for g in greetings:
            if re.search(r'\b' + re.escape(g) + r'\b', text_lower):
                if not any(w in text_lower for w in ["track", "order", "show", "ring", "necklace", "earring"]):
                    return IntentAnalysis(intent="GREETING", extracted_entity="")

        # 2. Detect Order Tracking intent
        is_tracking = False
        has_order_pattern = re.search(r'\b(?:sj|bb|trk)\s*-?\s*\d+\b', text_lower)
        has_general_digits = re.search(r'\b\d{5,}\b', text_lower)
        is_price_value = re.search(r'(?:under|below|less than|max|maximum|budget|rs\.?|inr|₹|\babove\b|\bmore than\b|\bover\b)\s*₹?\s*\d+', text_lower)
        
        if has_order_pattern or (has_general_digits and not is_price_value):
            is_tracking = True
        tracking_phrases = [
            "track my order", "order status", "check my order", "where is my order",
            "order tracking", "track order", "track order status", "check order status",
            "my order", "delivery status", "shipment status", "order update",
            "track package", "where is my package", "i want to track my order",
            "check my shipment", "order details", "my delivery", "track shipment",
            "tracking status", "shipment status", "package status"
        ]
        if any(p in text_lower for p in tracking_phrases) or (
            "where is" in text_lower and any(w in text_lower for w in ["package", "shipment", "delivery", "order"])
        ):
            is_tracking = True
  
        if is_tracking:
            order_id = ""
            order_match = re.search(r'\b(?:sj|bb|trk)\s*-?\s*\d+\b', text_lower)
            if not order_match and not is_price_value:
                order_match = re.search(r'\b\d{5,}\b', text_lower)
            if order_match:
                order_id = order_match.group().replace(" ", "").upper()
            cleaned_entity = self._clean_extracted_entity("ORDER_TRACKING", order_id)
            return IntentAnalysis(intent="ORDER_TRACKING", extracted_entity=cleaned_entity)
            
        # 3. Detect Support Ticket intent
        if any(w in text_lower for w in ["support", "ticket", "complaint", "issue", "help", "customer service", "need help", "damaged"]):
            issue = text.strip()
            for prefix in ["create ticket for", "create a support ticket for", "need support for", "issue with", "need help with", "complaint about"]:
                if prefix in issue.lower():
                    idx = issue.lower().find(prefix) + len(prefix)
                    issue = issue[idx:].strip()
                    break
            
            cleaned_entity = self._clean_extracted_entity("SUPPORT", issue)
            return IntentAnalysis(intent="SUPPORT", extracted_entity=cleaned_entity)

        # 4. Detect explicitly mentioned product categories
        categories_map = {
            "rings": "Ring",
            "ring": "Ring",
            "earrings": "Earrings",
            "earring": "Earrings",
            "necklaces": "Necklace",
            "necklace": "Necklace",
            "bracelets": "Bracelet",
            "bracelet": "Bracelet",
            "bangles": "Bangles",
            "bangle": "Bangles",
            "chains": "Chain",
            "chain": "Chain",
            "pendants": "Pendant",
            "pendant": "Pendant",
            "bridal": "Bridal Collection"
        }
        
        detected_cat = None
        for keyword, cat in categories_map.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                detected_cat = cat
                break

        # Surprise me detection
        if "surprise me" in text_lower or "recommend" in text_lower:
            return IntentAnalysis(intent="SURPRISE_ME", extracted_entity="")

        # Shopping Assistance detection
        shopping_keywords = {
            "need jewellery", "want jewellery", "buy jewellery", "need jewelry", "want jewelry", "buy jewelry",
            "buy a gift", "buy gift", "need a gift", "gift for", "don't know what to buy", "dont know what to buy",
            "help me choose", "i need to buy", "i need jewelry", "i want to buy", "need some jewelry", "need some jewellery",
            "for my wife", "for my mother", "for my sister", "for my friend", "for bride", "for wife",
            "for sister", "for mother"
        }
        
        occasions = {
            "wedding", "engagement", "proposal", "anniversary", "birthday", "festival",
            "daily wear", "office wear", "party wear", "luxury", "minimal", "traditional", "modern", "bridal"
        }
        
        is_shopping = any(k in text_lower for k in shopping_keywords) or text_lower in occasions
        
        if is_shopping:
            is_search = any(w in text_lower for w in ["under", "below", "price", "only", "ring", "necklace", "earring", "bracelet", "bangle", "chain", "pendant"])
            if not is_search:
                return IntentAnalysis(intent="SHOPPING_ASSISTANCE", extracted_entity=text)

        is_followup_filter = any(w in text_lower for w in ["gold", "silver", "diamond", "under", "below", "price", "only", "first", "second", "third", "one", "two", "three", "open"])
        
        target_category = detected_cat
        if not target_category and is_followup_filter and current_category:
            target_category = current_category

        is_product_search = any(w in text_lower for w in ["show", "find", "search", "buy", "looking for", "get", "product", "jewellery", "gold", "silver", "diamond", "price", "under", "below"])
        
        if target_category or is_product_search:
            return IntentAnalysis(intent="PRODUCT_SEARCH", extracted_entity=text, category=target_category)

        # 5. Default to General Chat
        return IntentAnalysis(intent="GENERAL_CHAT", extracted_entity="")
