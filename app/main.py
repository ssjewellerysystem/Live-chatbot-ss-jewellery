from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions import ChatbotException
from app.webhook import router as webhook_router
from app.config import settings

# Initialize the FastAPI Application
app = FastAPI(
    title="SSJewellery WhatsApp Chatbot API",
    description="Stage 1 backend connecting Meta's WhatsApp Cloud API with Google Gemini API.",
    version="1.0.0"
)

from app.database.connection import DatabaseConnectionManager

@app.on_event("startup")
async def startup_db_client():
    await DatabaseConnectionManager.initialize()

@app.on_event("shutdown")
async def shutdown_db_client():
    await DatabaseConnectionManager.close()


# Register custom global exception handler
@app.exception_handler(ChatbotException)
async def chatbot_exception_handler(request: Request, exc: ChatbotException) -> JSONResponse:
    """
    Globally catches ChatbotException and subclasses.
    Returns clean, structured JSON errors with correct status codes.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message
            }
        }
    )


from fastapi.staticfiles import StaticFiles

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register Webhook Router
app.include_router(webhook_router)


# Root/Health endpoint
@app.get("/", tags=["Health"])
async def root_health() -> dict:
    """
    Service health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "SSJewellery WhatsApp Chatbot",
        "stage": 1,
        "verify_token": settings.VERIFY_TOKEN
    }
