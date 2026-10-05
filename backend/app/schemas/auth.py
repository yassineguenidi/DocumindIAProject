from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
CompanyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


def check_password_rules(v: str) -> str:
    if len(v.encode("utf-8")) > 72:  # limite de bcrypt
        raise ValueError("Mot de passe trop long (72 octets max)")
    if not (any(c.islower() for c in v) and any(c.isupper() for c in v) and any(c.isdigit() for c in v)):
        raise ValueError("Le mot de passe doit contenir une majuscule, une minuscule et un chiffre")
    return v


class RegisterRequest(BaseModel):
    first_name: Name
    last_name: Name
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)
    company_name: CompanyName

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return check_password_rules(v)


class ProfileUpdate(BaseModel):
    first_name: Name
    last_name: Name
    company_name: Optional[CompanyName] = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=10, max_length=72)

    @field_validator("new_password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return check_password_rules(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    company_id: int
    company_name: str
    plan: str
    has_password: bool = True


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=10, max_length=4096)    