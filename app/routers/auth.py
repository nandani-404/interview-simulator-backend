from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, Token,
    UpdateProfile, ChangePassword, UserProfileResponse
)
from app.services.auth_service import (
    register_user, authenticate_user, create_access_token,
    get_user_by_email, hash_password, verify_password
)
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db)
):
    from app.models.user import User
    from app.services.auth_service import hash_password
    user = db.query(User).filter(User.email == "default@example.com").first()
    if not user:
        user = User(
            full_name="Default User",
            email="default@example.com",
            hashed_password=hash_password("DefaultPassword123!")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(db, user_data.full_name, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    created_at = current_user.created_at.strftime("%Y-%m-%d") if current_user.created_at else "N/A"
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": created_at
    }


@router.put("/update")
def update_profile(
    data: UpdateProfile,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    current_user.full_name = data.full_name
    db.commit()
    db.refresh(current_user)
    return {
        "message": "Profile updated successfully",
        "full_name": current_user.full_name
    }


@router.put("/change-password")
def change_password(
    data: ChangePassword,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters"
        )
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}