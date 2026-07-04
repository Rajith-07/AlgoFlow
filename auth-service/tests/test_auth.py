import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import jwt

# Add the project root to sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.config.config import settings
from app.db.database import get_db
from app.security.password import hash_password, verify_password
from app.security.jwt import (
    create_access_token,
    decode_access_token,
    get_jwks,
    load_keys,
    get_public_key,
    get_private_key,
)
from app.services.auth import hash_token
from app.models.user import User, RefreshToken

# Ensure keys are loaded/generated for testing
load_keys()


class TestSecurityHelpers(unittest.TestCase):
    def test_password_hashing(self):
        """Test Argon2 password hashing and verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$argon2id$"))
        
        # Verification
        self.assertTrue(verify_password(hashed, password))
        self.assertFalse(verify_password(hashed, "wrong_password"))

    def test_jwt_generation_and_decoding(self):
        """Test RS256 JWT generation, structure, and decoding."""
        user_id = "11111111-2222-3333-4444-555555555555"
        username = "testuser"
        role = "ADMIN"
        
        token = create_access_token(user_id=user_id, username=username, role=role)
        self.assertTrue(isinstance(token, str))
        
        # Verify kid in header
        headers = jwt.get_unverified_header(token)
        self.assertEqual(headers.get("kid"), "auth-service-key")
        self.assertEqual(headers.get("alg"), "RS256")
        
        # Decode and verify payload claims
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], user_id)
        self.assertEqual(payload["username"], username)
        self.assertEqual(payload["role"], role)
        self.assertTrue("iat" in payload)
        self.assertTrue("exp" in payload)

    def test_jwt_expiry(self):
        """Test that expired JWTs raise an InvalidTokenError."""
        # Temporarily mock expiration to be negative
        with patch("app.security.jwt.settings") as mock_settings:
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = -5
            mock_settings.JWT_ALGORITHM = "RS256"
            
            token = create_access_token("some_id", "some_user")
            
            with self.assertRaises(jwt.InvalidTokenError) as ctx:
                decode_access_token(token)
            self.assertIn("expired", str(ctx.exception).lower())

    def test_jwks_formatting(self):
        """Test that the JWKS output matches the RFC 7517 structure."""
        jwks = get_jwks()
        self.assertIn("keys", jwks)
        self.assertEqual(len(jwks["keys"]), 1)
        
        key = jwks["keys"][0]
        self.assertEqual(key["kty"], "RSA")
        self.assertEqual(key["alg"], "RS256")
        self.assertEqual(key["use"], "sig")
        self.assertEqual(key["kid"], "auth-service-key")
        self.assertTrue("n" in key)
        self.assertTrue("e" in key)


class TestEndpoints(unittest.TestCase):
    def setUp(self):
        # We use a mocked database session
        self.mock_db = AsyncMock()
        
        # Override the database dependency in FastAPI
        app.dependency_overrides[get_db] = lambda: self.mock_db
        
        # We import TestClient inside setup to avoid premature configuration
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def tearDown(self):
        # Clean up dependency overrides
        app.dependency_overrides.clear()

    @patch("app.services.auth.signup_user")
    def test_signup_endpoint(self, mock_signup):
        """Test POST /signup endpoint router."""
        mock_user = User(
            id="11111111-2222-3333-4444-555555555555",
            username="rajith",
            email="rajith@example.com",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        mock_signup.return_value = mock_user
        
        payload = {
            "username": "rajith",
            "email": "rajith@example.com",
            "password": "supersecurepassword"
        }
        
        response = self.client.post("/signup", json=payload)
        self.assertEqual(response.status_code, 201)  # 201 Created
        
        data = response.json()
        self.assertEqual(data["username"], "rajith")
        self.assertEqual(data["email"], "rajith@example.com")
        self.assertTrue("id" in data)

    @patch("app.services.auth.login_user")
    def test_login_endpoint(self, mock_login):
        """Test POST /login endpoint router."""
        mock_login.return_value = {
            "access_token": "mocked_access_token",
            "refresh_token": "mocked_refresh_token",
            "expires_in": 900
        }
        
        payload = {
            "email": "rajith@example.com",
            "password": "supersecurepassword"
        }
        
        response = self.client.post("/login", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["access_token"], "mocked_access_token")
        self.assertEqual(data["refresh_token"], "mocked_refresh_token")
        self.assertEqual(data["expires_in"], 900)

    @patch("app.services.auth.refresh_access_token")
    def test_refresh_endpoint(self, mock_refresh):
        """Test POST /refresh endpoint router."""
        mock_refresh.return_value = {
            "access_token": "new_mocked_access_token",
            "expires_in": 900
        }
        
        payload = {
            "refresh_token": "opaque_refresh_token"
        }
        
        response = self.client.post("/refresh", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["access_token"], "new_mocked_access_token")
        self.assertEqual(data["expires_in"], 900)

    @patch("app.services.auth.logout_user")
    def test_logout_endpoint(self, mock_logout):
        """Test POST /logout endpoint router."""
        mock_logout.return_value = None
        
        payload = {
            "refresh_token": "opaque_refresh_token"
        }
        
        response = self.client.post("/logout", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Successfully logged out"})

    def test_jwks_endpoint(self):
        """Test GET /.well-known/jwks.json endpoint router."""
        response = self.client.get("/.well-known/jwks.json")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("keys", data)
        self.assertEqual(data["keys"][0]["kid"], "auth-service-key")


if __name__ == "__main__":
    unittest.main()
