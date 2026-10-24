# API Guide and Evidence Checklist

Open Swagger at `http://127.0.0.1:8000/docs`.

## Login
1. `POST /auth/request-otp` body `{"mobile":"9876543210"}`.
2. In development only, read the code from `runtime/dev_otp.txt`. It is not returned by the API.
3. `POST /auth/verify-otp` body `{"mobile":"9876543210","otp":"<current code>"}`.
4. Click Authorize in Swagger and enter `Bearer <access_token>`.

## Endpoints
- `GET /health`: health status.
- `POST /auth/request-otp`: request OTP.
- `POST /auth/verify-otp`: verify OTP and obtain token.
- `GET /me`: authenticated customer.
- `GET /invoices`: own invoices only.
- `POST /conversations`: body `{"title":"Invoice questions"}`.
- `GET /conversations`: own conversations only.
- `GET /conversations/{id}/messages`: own conversation messages only.
- `POST /conversations/{id}/messages`: body `{"content":"What unpaid invoices do I have?"}`.
- Confirm a proposed invoice with body `{"content":"I confirm this invoice","confirm_invoice":true,"pending_invoice":{"invoice_number":"INV-300","invoice_date":"2026-10-22","amount":"1250","currency":"INR","payment_status":"unpaid"}}`.
- `GET /debug/vector-search?query=INV-300`: authenticated owner's vector results.
- `POST /admin/reindex`: retries indexing for authenticated customer's invoices.

All customer data endpoints require a valid bearer token. The server derives ownership from the token, not from a client-supplied customer ID.

### Required Screenshots

Capture screenshots from the actual running application for the following completed tests:

1. Swagger UI showing the available API endpoints.
2. OTP request and successful login for a seeded customer.
3. Authorized `/me` endpoint returning customer details.
4. `/invoices` endpoint returning the customer's invoices.
5. Successful conversation creation with HTTP 200.
6. Chatbot answering an invoice question with HTTP 200 and returning five invoice records.
7. Qdrant `customer_records` collection and successful vector search results.

### Tests Pending Verification

The following tests must be performed before they can be reported as successful:

- Invalid, expired, or reused OTP and resend cooldown.
- Customer data isolation between Arun and Deepa.
- Invoice confirmation and duplicate-creation prevention.
- Indexing failure and recovery using `/admin/reindex`.
- Additional authentication, error-handling, and security tests.

Use screenshots from the actual running implementation only. Hide secrets and OTP contents in any screenshot.
