from app.services.conversation_service import ConversationService

class AIService:
    """
    Orchestration service (Facade pattern) that wraps ConversationService
    to preserve backward compatibility with Stage 2 interfaces.
    """
    def __init__(self) -> None:
        self.conversation_service = ConversationService()

    async def process_user_message(self, message_text: str, sender_name: str, sender_phone: str = "919829276750") -> str:
        """
        Processes a user message by delegating to the conversation flow manager.
        """
        return await self.conversation_service.handle_message(
            sender_phone=sender_phone,
            message_text=message_text,
            sender_name=sender_name
        )
