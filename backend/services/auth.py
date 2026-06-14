import base64
import json
import hmac
import hashlib
import time
import os
from typing import List, Optional
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.db import get_db
from models.user import User

# Use a secure secret key, falling back to a default for development
JWT_SECRET = getattr(settings, "JWT_SECRET", "omniseek-super-secret-production-key-2026")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600 * 24 # 24 hours

security_bearer = HTTPBearer(auto_error=False)

class AuthService:
    """Authentication and authorization services utilizing custom JWT tokens and secure hashing."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 and PBKDF2 with a secure random salt."""
        salt = os.urandom(16)
        db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return f"{salt.hex()}:{db_hash.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password matching against salted hash."""
        try:
            salt_hex, hash_hex = password_hash.split(':')
            salt = bytes.fromhex(salt_hex)
            db_hash = bytes.fromhex(hash_hex)
            check_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(check_hash, db_hash)
        except Exception:
            return False

    @staticmethod
    def base64url_encode(data: bytes) -> str:
        """Helper to URL-safe base64 encode data."""
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    @staticmethod
    def base64url_decode(data: str) -> bytes:
        """Helper to URL-safe base64 decode data."""
        padding = '=' * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    @classmethod
    def create_access_token(cls, username: str, role: str) -> str:
        """Create a signed JWT access token containing subject and role payload."""
        header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
        payload = {
            "sub": username,
            "role": role,
            "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS
        }
        
        header_b64 = cls.base64url_encode(json.dumps(header).encode('utf-8'))
        payload_b64 = cls.base64url_encode(json.dumps(payload).encode('utf-8'))
        
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(JWT_SECRET.encode('utf-8'), message, hashlib.sha256).digest()
        signature_b64 = cls.base64url_encode(signature)
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @classmethod
    def decode_access_token(cls, token: str) -> Optional[dict]:
        """Decode and cryptographically verify a JWT access token."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature_b64 = parts
            
            # Recalculate signature and compare
            message = f"{header_b64}.{payload_b64}".encode('utf-8')
            expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), message, hashlib.sha256).digest()
            actual_sig = cls.base64url_decode(signature_b64)
            if not hmac.compare_digest(expected_sig, actual_sig):
                return None
            
            payload = json.loads(cls.base64url_decode(payload_b64).decode('utf-8'))
            if payload.get("exp", 0) < time.time():
                return None # Token has expired
                
            return payload
        except Exception:
            return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI dependency injecting the authenticated user model."""
    if not credentials:
        # Check if the database has the default admin user
        # We auto-create/fallback to the default admin user for local development and demo purposes,
        # since the frontend does not have client-side auth UI.
        import uuid
        from datetime import datetime
        stmt = select(User).filter(User.username == "admin")
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                username="admin",
                password_hash=AuthService.hash_password("admin"),
                role="ADMIN",
                created_at=datetime.utcnow()
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    token = credentials.credentials
    payload = AuthService.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload["sub"]
    stmt = select(User).filter(User.username == username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user record not found",
        )
    return user

def require_role(allowed_roles: List[str]):
    """Authorization dependency restricting endpoint execution to specific roles."""
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: permissions not granted for your role",
            )
        return user
    return dependency
