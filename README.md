# AlgoFlow AI Platform

AlgoFlow AI is a microservices-based Remote Code Execution (RCE) and competitive programming platform. The project is structured as a monorepo containing independent services communicating asynchronously and secured via standard cryptographic protocols.

## Repository Structure

```text
AlgoFlow_AI/
├── auth-service/                  # Authentication & Identity Microservice (Port 8000)
│   ├── app/                       # Core FastAPI application source code
│   ├── keys/                      # RS256 signing keys (private.pem / public.pem)
│   ├── migrations/                # Alembic database migrations
│   ├── tests/                     # Unit and integration test suite
│   ├── Dockerfile                 # Docker configuration
│   └── requirements.txt           # Service dependencies
│
├── submission-gateway-service/    # Submission Gateway Microservice (Port 8001)
│   ├── routers/                   # Endpoint routers
│   └── .env                       # Environment configuration
│
├── .gitignore                     # Git ignore file (excludes keys, .env, envs)
└── README.md                      # Overall project documentation (this file)
```

---

## Services Overview

### 1. Authentication & Identity Service (`auth-service`)
- **Port**: `8000`
- **Tech Stack**: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Argon2id, RS256 JWT.
- **Responsibilities**: User signup, user login, token-based authentication, refresh token rotation, token revocation (logout), and public key publication via JWKS (`/.well-known/jwks.json`).
- **Documentation**: See [auth-service/README.md](file:///d:/College/Portfolio%20Projects/AlgoFlow_AI/auth-service/README.md) for detailed setup and API specs.

### 2. Submission Gateway Service (`submission-gateway-service`)
- **Port**: `8001`
- **Tech Stack**: FastAPI, MongoDB, RabbitMQ.
- **Responsibilities**: Entry point for code submissions, queueing execution tasks, and routing traffic.

---

## Local Setup & Development

Detailed installation instructions for each microservice are provided in their respective directories. 

Generally, for any service:
1. Navigate to the service folder (e.g., `cd auth-service`).
2. Set up a Python virtual environment: `python -m venv venv`.
3. Activate the virtual environment:
   - On Windows: `.\venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`.
5. Configure environment variables in `.env` (using `.env.example` as a guide).
6. Run migrations (if applicable).
7. Start the service: `uvicorn app.main:app --reload --port <PORT>`.

---

## Architecture Design Principles

- **Separation of Concerns**: Services operate independently with dedicated databases. The Authentication service owns user identity, while the execution/submission service manages code runners.
- **Asymmetric JWT Verification (RS256)**: The `auth-service` holds the private key and signs tokens. Consuming services (like Gateway) retrieve the public key dynamically via the JWKS endpoint (`/.well-known/jwks.json`) and verify access tokens locally without hitting the database or the auth service.
- **Opaque Refresh Tokens**: To maximize security, refresh tokens are secure random strings. Only their SHA-256 hashes are stored, preventing token leakage in case of database compromise.
