import json
from google import genai
from google.genai import types
from google.genai import errors

from app.config import settings
from app.exceptions import GeminiAPIError


class GeminiClient:
    """
    Client wrapper for communicating with Google Gemini API asynchronously.
    """
    def __init__(self) -> None:
        # Initialize the Google Gen AI client with the Gemini API key
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def generate_ai_response(self, user_message: str, sender_name: str, history: list = None, context: dict = None) -> str:
        """
        Sends the user message along with sender context, conversation history, and
        structured conversation context to Gemini and fetches the response.
        Raises GeminiAPIError if any API, network, or validation exception occurs.
        """
        try:
            # Format and prepend history if available
            history_str = ""
            if history:
                for msg in history[:-1]: # exclude the latest user message
                    role = "User" if msg["role"] == "user" else "Assistant"
                    history_str += f"{role}: {msg['text']}\n"
            
            context_str = json.dumps(context or {}, indent=2)
            
            prompt = (
                f"Structured Conversation Context:\n"
                f"{context_str}\n\n"
                f"Recent Conversation History:\n"
                f"{history_str or '(No previous history)'}\n\n"
                f"Latest User Message: {user_message}"
            )
            contents = [prompt]

            # Using gemini-2.5-flash as the default model (fast, multi-modal, and large context)
            response = await self.client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"You are a helpful customer service assistant for SSJewellery. "
                        f"You are talking to {sender_name}. Keep responses polite, concise, and helpful. "
                        f"Use the provided Structured Conversation Context and Recent Conversation History to answer the User. "
                        f"Never invent previous messages or guess conversation history."
                    ),
                    temperature=0.7,
                    max_output_tokens=500
                )
            )

            ai_text = response.text
            if not ai_text:
                raise GeminiAPIError("Received empty text response from Gemini API.")

            return ai_text.strip()

        except errors.APIError as exc:
            raise GeminiAPIError(f"Gemini API call failed: {str(exc)}")
        except Exception as exc:
            raise GeminiAPIError(f"Failed to communicate with Gemini: {str(exc)}")


# Alias to maintain architecture and webhook compatibility without modification
OpenAIClient = GeminiClient
