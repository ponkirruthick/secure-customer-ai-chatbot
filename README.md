# Secure Customer AI Chatbot

A secure customer-support chatbot built with FastAPI, PostgreSQL, Ollama, and Qdrant. It supports OTP authentication, customer-specific invoice access, and AI-powered invoice questions.

## Features
- OTP-based customer authentication
- JWT bearer-token authorization
- Customer-specific invoice retrieval
- AI-powered chat using Ollama
- Vector search using Qdrant
- PostgreSQL database with Alembic migrations
- API documentation through Swagger UI

## Tech Stack
Python · FastAPI · PostgreSQL · SQLAlchemy · Alembic · Qdrant · Ollama · JWT

## Setup
1. Install Python, PostgreSQL, Ollama, and Qdrant.
2. Create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

3. Configure your database connection and a strong `JWT_SECRET` in `.env`.
4. Start Qdrant and Ollama, and download the required models: `mistral` and `nomic-embed-text`.
5. Create the `customer_chatbot` PostgreSQL database.
6. Run migrations and seed sample data:

```powershell
alembic upgrade head
python -m app.seed
```

7. Start the API:

```powershell
python -m uvicorn app.main:app --reload
```

8. Open Swagger UI: http://127.0.0.1:8000/docs

## Documentation
- `docs/PROJECT_REPORT.md` — project report and limitations
- `docs/API_AND_TESTING.md` — API guide and testing checklist

## Security Notes
The development OTP adapter writes codes to `runtime/dev_otp.txt`. It is for local testing only, not production. Never commit `.env`, OTP files, passwords, or secret keys.

## Testing Status
Refer to the project report and testing checklist for verified results and tests still pending.
