# Authentication & Identity Service

This is the standalone **Authentication & Identity Microservice** for the **AlgoFlow AI** platform. It handles user registration, credentials validation, session issuance, and public-key cryptography management using FastAPI, PostgreSQL, SQLAlchemy, Alembic, Argon2id, and RS256 JWTs.

---

## Features

- **User Signup**: Registration validating uniqueness of username and email, hashing passwords via Argon2id.
- **User Login**: Credentials validation issuing a short-lived (15 min) RS256 Access JWT and a long-lived (30 days) opaque Refresh Token.
- **Token Rotation & Refresh**: `/refresh` endpoint validating opaque refresh tokens and generating new access tokens.
- **Token Revocation (Logout)**: Invalidation of refresh tokens by marking their database hashes as revoked.
- **JWKS Endpoint**: Standard OIDC endpoint (`/.well-known/jwks.json`) publishing the public RSA key for other microservices to locally verify access tokens.
- **Automated Key Management**: Automatic generation of 2048-bit RSA keys at startup if they are missing in the configured paths.

---

## Folder Structure

```text
auth-service/
├── app/
│   ├── api/                   # API Routers & Endpoints
│   │   ├── endpoints.py       # /signup, /login, /refresh, /logout
│   │   └── jwks.py            # /.well-known/jwks.json
│   │
│   ├── auth/                  # Authentication dependencies
│   │   └── dependencies.py    # get_current_user_claims (extracted from JWT)
│   │
│   ├── config/                # Environment variables configuration
│   │   └── config.py
│   │
│   ├── db/                    # Database Session management
│   │   └── database.py        # SQLAlchemy engine, session maker, Base class
│   │
│   ├── models/                # SQLAlchemy database models
│   │   └── user.py            # User and RefreshToken models
│   │
│   ├── schemas/               # Pydantic validation schemas
│   │   └── user.py            # Signup, login, and token models
│   │
│   ├── security/              # Hashing and token cryptography
│   │   ├── jwt.py             # RS256 token creation, decryption, & JWKS formatting
│   │   └── password.py        # Argon2id password hash & verification
│   │
│   └── main.py                # Service initialization and lifespan events
│
├── migrations/                # Alembic database migration scripts
│   ├── versions/              # Migration files
│   └── env.py                 # Async Alembic database connector
│
├── keys/                      # Auto-generated RSA keys (Ignored by Git)
│   ├── private.pem
│   └── public.pem
│
├── tests/                     # Unit and integration test suite
│   └── test_auth.py
│
├── Dockerfile                 # Docker container instructions
├── requirements.txt           # Python dependencies
└── alembic.ini                # Alembic configuration
```

---

## Local Setup

### 1. Set Up Environment Variables
Create a `.env` file in the root of the `auth-service/` directory (you can copy `.env.example` as a template):
```env
PROJECT_NAME="Auth Service"
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db"
JWT_PRIVATE_KEY_PATH="keys/private.pem"
JWT_PUBLIC_KEY_PATH="keys/public.pem"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ALGORITHM="RS256"
```

### 2. Configure Virtual Environment & Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Database Migrations
Make sure your PostgreSQL server is running and the database matches `DATABASE_URL`. Run the migrations using Alembic:
```bash
python -m alembic upgrade head
```

### 4. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
On startup, the service will automatically generate a new RSA 2048-bit keypair under `keys/` if it does not already exist.

---

## Testing

A complete unit and integration test suite is located in `tests/test_auth.py`. The tests mock database operations so they can be run locally without requiring a running database server.

Run the tests using:
```bash
python tests/test_auth.py
```

---

## API Documentation

Once the development server is running, you can explore the interactive API endpoints and schemas at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
