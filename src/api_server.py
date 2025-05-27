# src/api_server.py
import uuid  # For generating unique IDs

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from structlog import get_logger

logger = get_logger(__name__)


# --- User Model Definition ---
class UserBase(BaseModel):
    email: EmailStr
    username: str
    isAdmin: bool | None = False


class UserCreate(UserBase):
    password: str  # In a real app, this would be hashed


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    isAdmin: bool | None = None


class UserInDB(UserBase):
    id: str  # Using string UUIDs for IDs
    # In a real app, you wouldn't expose password hashes like this directly
    # password_hash: str


# --- Mock User Database ---
# Using a dictionary for easier lookups by ID
mock_user_db: dict[str, UserInDB] = {}


# Pre-populate with a couple of users for testing
def _init_mock_db():
    admin_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    mock_user_db[admin_id] = UserInDB(
        id=admin_id, email="admin@example.com", username="admin_user", isAdmin=True
    )
    mock_user_db[user_id] = UserInDB(
        id=user_id, email="user@example.com", username="normal_user", isAdmin=False
    )


_init_mock_db()  # Initialize DB on startup


app = FastAPI(
    title="Oil & Gas Futures API",
    description="API for managing oil and gas futures data and related services.",
    version="0.1.0",
)


# --- User Management API Endpoints (Mock Implementation) ---
@app.post(
    "/api/v1/users", response_model=UserInDB, status_code=status.HTTP_201_CREATED, tags=["Users"]
)
async def create_user(user_in: UserCreate):
    logger.info("Attempting to create user", email=user_in.email)
    if any(u.email == user_in.email for u in mock_user_db.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user_id = str(uuid.uuid4())
    # In a real app, hash user_in.password here
    new_user = UserInDB(
        id=user_id,
        email=user_in.email,
        username=user_in.username,
        isAdmin=user_in.isAdmin or False,  # Ensure isAdmin has a default
    )
    mock_user_db[user_id] = new_user
    logger.info("User created successfully", user_id=user_id, email=new_user.email)
    return new_user


@app.get("/api/v1/users", response_model=list[UserInDB], tags=["Users"])
async def get_users():
    logger.info(f"Fetching all users. Total: {len(mock_user_db)}")
    return list(mock_user_db.values())


@app.get("/api/v1/users/{user_id}", response_model=UserInDB, tags=["Users"])
async def get_user(user_id: str):
    logger.info("Fetching user by ID", user_id=user_id)
    user = mock_user_db.get(user_id)
    if not user:
        logger.warning("User not found for ID", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.put("/api/v1/users/{user_id}", response_model=UserInDB, tags=["Users"])
async def update_user(user_id: str, user_update: UserUpdate):
    logger.info("Attempting to update user", user_id=user_id)
    user = mock_user_db.get(user_id)
    if not user:
        logger.warning("User not found for update", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    # Check for email conflict if email is being updated
    if (
        "email" in update_data
        and update_data["email"] != user.email
        and any(u.email == update_data["email"] for u in mock_user_db.values())
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email already registered by another user",
        )

    updated_user = user.model_copy(update=update_data)
    mock_user_db[user_id] = updated_user
    logger.info("User updated successfully", user_id=user_id)
    return updated_user


@app.delete("/api/v1/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(user_id: str):
    logger.info("Attempting to delete user", user_id=user_id)
    if user_id not in mock_user_db:
        logger.warning("User not found for deletion", user_id=user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    del mock_user_db[user_id]
    logger.info("User deleted successfully", user_id=user_id)
    return  # For 204 No Content, FastAPI expects no return value


@app.get("/", tags=["Root"])
async def read_root():
    """Welcome endpoint for the API."""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Oil & Gas Futures API!"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    logger.info("Health check accessed")
    return {"status": "ok"}


# If you run this file directly using `python src/api_server.py` (for local dev without uvicorn CLI):
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
