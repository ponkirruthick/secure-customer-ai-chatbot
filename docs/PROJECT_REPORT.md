# Secure Customer AI Chatbot — Project Report

## 1. Objective
Create an authenticated assistant that answers questions about a customer's own invoices, remembers conversation history and creates invoices only after explicit confirmation.

## 2. Technology stack
Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Qdrant, Ollama chat model and embedding model, JWT bearer tokens.

## 3. Architecture
FastAPI exposes the API. OTP verification issues an expiring token. Each protected endpoint derives the customer identity from the token and filters database and vector queries to that customer. PostgreSQL is the source of truth; Qdrant stores embeddings and metadata.

## 4. Database
`customers` stores synthetic users; `invoices` stores invoice number/date/amount/currency/status and owner FK; `conversations` and `messages` persist chat memory; `otp_challenges` stores OTP hashes, expiry, attempts and consumption state. A unique constraint prevents duplicate invoice numbers per customer.

## 5. Security
Mobile numbers are normalized. OTP codes are randomly generated, hashed in PostgreSQL, expire in five minutes, allow at most five attempts, and have a 60-second resend cooldown. Tokens expire. Customer data endpoints require bearer authentication. Conversations and invoices are owner-filtered. Tool names are allowlisted. Invoice creation requires explicit confirmation and validates fields.

## 6. Retrieval and memory
Conversation messages persist in PostgreSQL and the recent-history window is configurable (`HISTORY_LIMIT`). Embeddings and owner/record identifiers are persisted in Qdrant. Vector searches apply a mandatory authenticated-owner filter. Retrieved context is passed separately to the model and not stored as a user message.

## 7. Invoice consistency
Invoices are committed to PostgreSQL before indexing. If indexing fails, the invoice remains saved and `indexed=false`; `/admin/reindex` retries indexing. Deterministic Qdrant point IDs make repeated indexing idempotent.

## 8. Setup
Follow `README.md`. Run migrations, seed synthetic records, start the API, and use Swagger at `/docs`.
### 9. Test Results

The Secure Customer AI Chatbot was tested locally using FastAPI Swagger UI.

**Tests completed successfully**
- FastAPI application started successfully, and Swagger UI was accessible.
- OTP authentication was tested using a seeded customer account.
- The authenticated `/me` endpoint returned customer details.
- The `/invoices` endpoint returned the logged-in customer's invoice records.
- A conversation was created successfully with HTTP 200.
- The chatbot answered the question “What invoices do I have?” with HTTP 200.
- The `search_records` tool executed successfully and returned five relevant invoice records.
- Qdrant was running, the `customer_records` collection was created, and vector search returned invoice records.

**Known limitations and pending checks**
- OTP delivery uses a local development file and is not production SMS delivery.
- The Qdrant Python client and server versions differ; compatibility should be verified.
- Additional security, error-handling, and invoice-confirmation tests are still required.
### 10. Limitations

1. **OTP delivery:** OTPs are stored in a local development file. A secure SMS or email delivery service is required for production use.
2. **Vector database:** Qdrant is running locally, and the `customer_records` collection has been created. Further testing is required to verify client-server compatibility and recovery after service interruptions.
3. **Local AI models:** The chatbot uses Ollama with the Mistral language model and the `nomic-embed-text` embedding model. Both depend on the local environment and available system resources.
4. **Security hardening:** Additional testing is needed for authentication, access control, invalid requests, and production configuration.
5. **Test coverage:** More automated tests are needed for error handling, invoice-related questions, and other customer scenarios.