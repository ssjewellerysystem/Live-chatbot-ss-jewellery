class ChatbotException(Exception):
    """Base exception for all application-specific errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class WebhookVerificationError(ChatbotException):
    """Raised when the WhatsApp hub.verify_token does not match ours."""
    def __init__(self, message: str = "Invalid verification token"):
        super().__init__(message, status_code=403)


class SignatureVerificationError(ChatbotException):
    """Raised when the incoming X-Hub-Signature-256 header is invalid."""
    def __init__(self, message: str = "X-Hub-Signature-256 validation failed"):
        super().__init__(message, status_code=401)


class InvalidPayloadError(ChatbotException):
    """Raised when the incoming request does not have the expected structure."""
    def __init__(self, message: str = "Invalid Webhook payload structure"):
        super().__init__(message, status_code=400)


class WhatsAppAPIError(ChatbotException):
    """Raised when the call to Meta's Graph API fails."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(f"WhatsApp API error: {message}", status_code)


class GeminiAPIError(ChatbotException):
    """Raised when the call to Google Gemini's generation API fails."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(f"Gemini API error: {message}", status_code)


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass

