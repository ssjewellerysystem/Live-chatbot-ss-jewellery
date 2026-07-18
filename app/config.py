from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings validated using Pydantic Settings.
    Ensures fail-fast behavior if any required environment variable is missing.
    """
    VERIFY_TOKEN: str = Field(..., description="Meta Webhook Verification Token")
    WHATSAPP_ACCESS_TOKEN: str = Field(..., description="Access Token for WhatsApp Cloud API")
    PHONE_NUMBER_ID: str = Field(..., description="WhatsApp Business Phone Number ID")
    APP_SECRET: str = Field(..., description="Meta App Secret for HMAC Signature Verification")
    GEMINI_API_KEY: str = Field(..., description="API Key for Google Gemini API")

    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model to use"
    )
    GEMINI_TEMPERATURE: float = Field(
        default=0.7,
        description="Gemini model temperature"
    )
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(
        default=500,
        description="Gemini model max output tokens"
    )
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL Database Connection URI"
    )
    SESSION_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Session inactivity timeout in seconds"
    )
    WEBSITE_URL: str = Field(
        default="https://ssjewellery.com",
        description="Main production website URL"
    )
    DEMO_WEBSITE_URL: str = Field(
        default="https://demo.ssjewellery.com",
        description="Demo/dev website URL for tracking"
    )
    WELCOME_LOGO_URL: str = Field(
        default="",
        description="SSJewellery Welcome Logo URL"
    )
    WELCOME_LOGO_CAPTION: str = Field(
        default=(
            "💎 Welcome to SSJewellery\n\n"
            "Hello, Sir/Madam! 👋\n\n"
            "Thank you for choosing SSJewellery.\n\n"
            "We're committed to providing you with an exceptional shopping experience.\n\n"
            "Our assistant is here to help you every step of the way.\n\n"
            "Available Services\n\n"
            "🔎 Explore Our Collection\n"
            "📦 Track Your Orders\n"
            "💬 Customer Support\n"
            "💎 Product Recommendations\n\n"
            "Please choose an option below to get started."
        ),
        description="SSJewellery Welcome Logo Caption"
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
