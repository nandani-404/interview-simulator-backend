from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class UpdateProfile(BaseModel):
    full_name: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True