from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.database.models import UserRole

# Shared properties
class UserBase(BaseModel):
    email: EmailStr

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.APPLICANT

# Properties to return to client
class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Properties for JWT Token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str | None = None
