from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.rate_limit import login_limiter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.schemas.auth import GoogleLoginRequest, PasswordChange, ProfileUpdate, RegisterRequest, TokenResponse, UserResponse

from app.api.deps import get_current_user
from app.db import get_db
from app.models import User
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role.value,
        company_id=user.company_id,
        company_name=user.company.name,
        plan=user.company.plan.code,
        has_password=user.has_password,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return to_response(auth_service.register(db, data))


@router.post("/google", response_model=TokenResponse)
def google_login(data: GoogleLoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    key = f"google:{ip}"
    login_limiter.check(key)
    try:
        info = auth_service.verify_google_credential(data.credential)
    except HTTPException as exc:
        if exc.status_code == 401:
            login_limiter.fail(key)
        raise
    return TokenResponse(access_token=auth_service.login_with_google(db, info))


@router.post("/login", response_model=TokenResponse)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}:{form.username.lower()}"
    login_limiter.check(key)
    try:
        token = auth_service.login(db, form.username, form.password)
    except HTTPException as exc:
        if exc.status_code == 401:
            login_limiter.fail(key)
        raise
    login_limiter.reset(key)
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return to_response(user)


@router.patch("/me", response_model=UserResponse)
def update_me(data: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_response(auth_service.update_profile(db, user, data))


@router.post("/change-password", status_code=204)
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.has_password:
        raise HTTPException(400, "Votre compte utilise la connexion Google : aucun mot de passe à modifier")

    key = f"pwd:{user.id}"
    login_limiter.check(key)  # même protection anti-brute-force que le login
    # Erreur 400 (et non 401) : un 401 déconnecterait l'utilisateur côté site
    if not verify_password(data.current_password, user.hashed_password):
        login_limiter.fail(key)
        raise HTTPException(400, "Mot de passe actuel incorrect")
    login_limiter.reset(key)
    auth_service.set_password(db, user, data.new_password)