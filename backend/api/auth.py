from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.db import get_db
from models.user import User
from services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field("USER", description="ADMIN or USER")

class LoginRequest(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str

@router.post("/register", response_model=Dict[str, str])
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Register a new application user account securely with password hash PBKDF2."""
    role_upper = payload.role.upper()
    if role_upper not in {"ADMIN", "USER"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be ADMIN or USER"
        )
        
    # Check if username exists
    stmt = select(User).filter(User.username == payload.username)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    password_hash = AuthService.hash_password(payload.password)
    new_user = User(
        username=payload.username,
        password_hash=password_hash,
        role=role_upper
    )
    db.add(new_user)
    await db.commit()
    
    return {"message": "User registered successfully", "username": payload.username}

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Validate credentials and issue signed JWT access tokens."""
    stmt = select(User).filter(User.username == payload.username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user or not AuthService.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = AuthService.create_access_token(user.username, user.role)
    return TokenResponse(
        access_token=access_token,
        username=user.username,
        role=user.role
    )
