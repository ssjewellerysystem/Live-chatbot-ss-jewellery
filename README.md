# SSJewellery WhatsApp AI Chatbot - Stage 1

An asynchronous, modular backend application built using Python, FastAPI, and Uvicorn. This service connects Meta's WhatsApp Cloud API with Google's Gemini API.

---

## Architecture & Design

This project is built following Clean Architecture guidelines and SOLID principles to ensure it is easily extendable for future database integrations (PostgreSQL), task queues (Celery), and agentic workflows (RAG / Function Calling).

### Project Layout
```
chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entrypoint & global exception handlers
│   ├── config.py            # Type-checked settings management with Pydantic Settings
│   ├── webhook.py           # Webhook routes (verification & event reception)
│   ├── whatsapp_client.py   # Async HTTP client wrapper for Meta Graph API
│   ├── ai_client.py         # Async Google Gemini SDK client
│   ├── schemas.py           # Pydantic validation schemas for inbound/outbound payloads
│   ├── exceptions.py        # Custom domain exception classes
│   └── utils.py             # Helper tools (cryptographic validation, text extraction)
│
├── .env                     # Local secrets (ignored by Git)
├── .env.example             # Template for local configurations
├── requirements.txt         # Project package dependencies
├── .gitignore               # Excludes virtual environments and credentials
└── README.md                # Setup & configuration guide
```

### Request Flow
1. **Meta Webhook Hook**: Meta sends user messages to our endpoint `/webhook` via `POST`.
2. **Signature Verification**: We compute the SHA-256 HMAC of the raw body using the `APP_SECRET` to verify that the message originated from Meta.
3. **Payload Parsing**: The JSON is parsed and validated using robust, nested Pydantic models in `app/schemas.py`.
4. **AI Generation**: If the request contains a text message, we invoke Google's `gemini-2.5-flash` model via an asynchronous call.
5. **WhatsApp Transmission**: We send the generated response back to the sender's phone number via Meta's Graph API.
6. **HTTP Response**: The endpoint returns `HTTP 200 OK` to confirm receipt.

---

## Installation & Setup

### Prerequisites
* Python 3.12 or higher installed.

### Steps
1. **Clone & Open Project Workspace**:
   ```bash
   cd /home/irshad-mohammad/Videos/Chatbot
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your actual credentials:
   ```bash
   cp .env.example .env
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Uvicorn Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The local server will start at `http://127.0.0.1:8000`.

---

## Connecting Meta WhatsApp Cloud API

To receive and respond to real messages, you must expose your local port `8000` to the internet (using tools like `ngrok` or Cloudflare Tunnels) and register it in the Meta Developer Portal.

1. **Expose Server**:
   ```bash
   ngrok http 8000
   ```
   Copy the HTTPS URL generated (e.g., `https://xxxx.ngrok-free.app`).

2. **Configure Webhook in Meta Portal**:
   * Navigate to the [Meta Developer Portal](https://developers.facebook.com/).
   * Select your App -> **WhatsApp** -> **Configuration**.
   * Under **Webhook**, click **Edit**.
   * Set **Callback URL** to `https://xxxx.ngrok-free.app/webhook`.
   * Set **Verify Token** to the exact value of `VERIFY_TOKEN` in your `.env`.
   * Click **Verify and Save**.

3. **Subscribe to Webhook Fields**:
   * Under the Webhook settings page in the portal, find the **Webhook fields** table.
   * Click **Subscribe** next to **messages**.

4. **Test Sending a Message**:
   * Send a text message to your WhatsApp Business Test Phone number.
   * Check your terminal logs. The chatbot will receive the message, request Gemini, and reply.
# whatsapp_chatbot
