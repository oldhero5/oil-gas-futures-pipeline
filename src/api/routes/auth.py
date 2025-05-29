"""Authentication API endpoints."""

import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from structlog import get_logger

from src.api.models import Token, User, UserCreate, UserLogin
from src.storage.operations import DatabaseOperations

logger = get_logger()
router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def get_db() -> DatabaseOperations:
    """Dependency to get database connection."""
    db = DatabaseOperations()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"user_id": user_id, "email": payload.get("email")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


@router.post("/register", response_model=User)
async def register(user_data: UserCreate, db: DatabaseOperations = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        query = "SELECT * FROM users WHERE email = ?"
        result = db.conn.execute(query, [user_data.email]).fetchone()

        if result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Insert new user
        insert_query = """
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
            RETURNING *
        """

        user_row = db.conn.execute(
            insert_query, [user_data.email, password_hash, user_data.full_name, "viewer"]
        ).fetchone()

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user"
            )

        # Convert to dict
        columns = [
            "user_id",
            "email",
            "password_hash",
            "full_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
            "last_login",
        ]
        user_dict = dict(zip(columns, user_row))

        return User(
            user_id=str(user_dict["user_id"]),
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            role=user_dict["role"],
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
            last_login=user_dict["last_login"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to register user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: DatabaseOperations = Depends(get_db)):
    """Login user and return JWT token."""
    try:
        # Find user
        query = "SELECT * FROM users WHERE email = ?"
        result = db.conn.execute(query, [user_data.email]).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        # Convert to dict
        columns = [
            "user_id",
            "email",
            "password_hash",
            "full_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
            "last_login",
        ]
        user_dict = dict(zip(columns, result))

        # Verify password
        if not verify_password(user_data.password, user_dict["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        # Check if user is active
        if not user_dict["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled"
            )

        # Update last login
        update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?"
        db.conn.execute(update_query, [user_dict["user_id"]])

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_dict["user_id"]), "email": user_dict["email"]},
            expires_delta=access_token_expires,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to login user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to login"
        )


@router.get("/me", response_model=User)
async def get_current_user(
    current_user=Depends(verify_token), db: DatabaseOperations = Depends(get_db)
):
    """Get current user information."""
    try:
        query = "SELECT * FROM users WHERE user_id = ?"
        result = db.conn.execute(query, [current_user["user_id"]]).fetchone()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Convert to dict
        columns = [
            "user_id",
            "email",
            "password_hash",
            "full_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
            "last_login",
        ]
        user_dict = dict(zip(columns, result))

        return User(
            user_id=str(user_dict["user_id"]),
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            role=user_dict["role"],
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
            last_login=user_dict["last_login"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get current user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information",
        )


@router.post("/logout")
async def logout(current_user=Depends(verify_token)):
    """Logout user (client should discard token)."""
    # In a more sophisticated implementation, we might blacklist the token
    # For now, just return success and let client discard the token
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user=Depends(verify_token), db: DatabaseOperations = Depends(get_db)
):
    """Refresh JWT token."""
    try:
        # Verify user still exists and is active
        query = "SELECT is_active FROM users WHERE user_id = ?"
        result = db.conn.execute(query, [current_user["user_id"]]).fetchone()

        if not result or not result[0]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user["user_id"], "email": current_user["email"]},
            expires_delta=access_token_expires,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to refresh token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh token"
        )
