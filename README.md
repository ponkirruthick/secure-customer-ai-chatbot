# Secure Customer AI Chatbot

FastAPI + PostgreSQL + Alembic + Qdrant + Ollama.

## Windows quick start
1. Install Python 3.11+, PostgreSQL, Docker Desktop, and Ollama.
2. Extract ZIP; open folder in VS Code.
3. PowerShell:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Edit `.env`: set PostgreSQL password and a long random `JWT_SECRET`.
5. Start Qdrant:
   ```powershell
   docker run -d --name chatbot-qdrant -p 6333:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant
   ```
6. In another terminal, run `ollama pull mistral` and `ollama pull nomic-embed-text`.
7. Create a PostgreSQL database named `customer_chatbot`.
8. Run:
   ```powershell
   alembic upgrade head
   python -m app.seed
   uvicorn app.main:app --reload
   ```
9. Visit http://127.0.0.1:8000/docs

OTPs in development are delivered to `runtime/dev_otp.txt`, not returned by the API. Never use this development adapter in production. See `docs/API_AND_TESTING.md` and `docs/PROJECT_REPORT.md`.

This is a starter implementation: run the required local verification checklist and record real test results before submitting.
