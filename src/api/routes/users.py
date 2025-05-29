"""User management API endpoints (admin only)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from structlog import get_logger

from src.api.models import User
from src.api.routes.auth import get_db, verify_token
from src.storage.operations import DatabaseOperations

logger = get_logger()
router = APIRouter(prefix="/api/users", tags=["users"])


def verify_admin(current_user=Depends(verify_token), db: DatabaseOperations = Depends(get_db)):
    """Verify current user is an admin."""
    query = "SELECT role FROM users WHERE user_id = ?"
    result = db.conn.execute(query, [current_user["user_id"]]).fetchone()

    if not result or result[0] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return current_user


@router.get("", response_model=list[User])
async def list_users(
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user=Depends(verify_admin),
    db: DatabaseOperations = Depends(get_db),
):
    """List all users (admin only)."""
    try:
        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if role is not None:
            query += " AND role = ?"
            params.append(role)

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = db.conn.execute(query, params).fetchall()

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

        users = []
        for row in results:
            user_dict = dict(zip(columns, row))
            users.append(
                User(
                    user_id=str(user_dict["user_id"]),
                    email=user_dict["email"],
                    full_name=user_dict["full_name"],
                    role=user_dict["role"],
                    is_active=user_dict["is_active"],
                    created_at=user_dict["created_at"],
                    last_login=user_dict["last_login"],
                )
            )

        return users

    except Exception as e:
        logger.error("Failed to list users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str, current_user=Depends(verify_admin), db: DatabaseOperations = Depends(get_db)
):
    """Get specific user details (admin only)."""
    try:
        query = "SELECT * FROM users WHERE user_id = ?"
        result = db.conn.execute(query, [user_id]).fetchone()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
        logger.error("Failed to get user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    full_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    current_user=Depends(verify_admin),
    db: DatabaseOperations = Depends(get_db),
):
    """Update user details (admin only)."""
    try:
        # Build update query
        updates = []
        params = []

        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)

        if role is not None:
            if role not in ["admin", "editor", "viewer"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role. Must be admin, editor, or viewer",
                )
            updates.append("role = ?")
            params.append(role)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)

        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ? RETURNING *"
        result = db.conn.execute(query, params).fetchone()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
        logger.error("Failed to update user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str, current_user=Depends(verify_admin), db: DatabaseOperations = Depends(get_db)
):
    """Delete a user (admin only)."""
    try:
        # Prevent admin from deleting themselves
        if user_id == current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
            )

        # Check if user exists
        check_query = "SELECT COUNT(*) FROM users WHERE user_id = ?"
        count = db.conn.execute(check_query, [user_id]).fetchone()[0]

        if count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Delete user sessions first (foreign key constraint)
        db.conn.execute("DELETE FROM user_sessions WHERE user_id = ?", [user_id])

        # Delete user audit logs
        db.conn.execute("DELETE FROM user_audit_log WHERE user_id = ?", [user_id])

        # Delete user
        db.conn.execute("DELETE FROM users WHERE user_id = ?", [user_id])

        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user"
        )
