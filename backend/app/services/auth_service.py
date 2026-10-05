from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models import Company, User, UserRole
from app.repositories import user_repository, plan_repository
from app.schemas.auth import RegisterRequest, ProfileUpdate 


import secrets

from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.exc import IntegrityError

from app.core.config import settings

def register(db: Session, data: RegisterRequest) -> User:
    if user_repository.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cet email est déjà utilisé")

    free_plan = plan_repository.get_by_code(db, "free")
    if free_plan is None:
        raise HTTPException(500, "Plans non initialisés (lance seed_plans)")

    company = Company(name=data.company_name, plan_id=free_plan.id)
    db.add(company)
    db.flush()  # récupère company.id sans valider

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        role=UserRole.ADMIN,
        company_id=company.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> str:
    user = user_repository.get_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_access_token(user.id)


def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    user.first_name = data.first_name
    user.last_name = data.last_name
    if data.company_name is not None:
        if user.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Seul un administrateur peut modifier l'entreprise")
        user.company.name = data.company_name
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user: User, new_password: str) -> None:
    if verify_password(new_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le nouveau mot de passe doit être différent de l'actuel")
    user.hashed_password = hash_password(new_password)
    db.commit()

def verify_google_credential(credential: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Connexion Google non configurée")
    try:
        info = id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID, clock_skew_in_seconds=10
        )
    except google_exceptions.TransportError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Impossible de contacter Google. Réessayez.")
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Connexion Google invalide")
    if not info.get("email") or not info.get("email_verified"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "L'adresse email de ce compte Google n'est pas vérifiée")
    return info


def login_with_google(db: Session, info: dict) -> str:
    sub = info["sub"]
    email = info["email"].lower()
    user = user_repository.get_by_google_sub(db, sub)

    if user is None:
        if user_repository.get_by_email(db, email):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Un compte existe déjà avec cet email. Connectez-vous avec votre mot de passe.",
            )
        free_plan = plan_repository.get_by_code(db, "free")
        if free_plan is None:
            raise HTTPException(500, "Plans non initialisés (lance seed_plans)")

        first = (info.get("given_name") or email.split("@")[0])[:100]
        company = Company(name=f"Entreprise de {first}"[:200], plan_id=free_plan.id)
        db.add(company)
        db.flush()
        user = User(
            first_name=first,
            last_name=(info.get("family_name") or "")[:100],
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # inconnu de tous
            has_password=False,
            google_sub=sub,
            role=UserRole.ADMIN,
            company_id=company.id,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "Création du compte en cours, réessayez dans un instant")
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Compte désactivé")
    return create_access_token(user.id)    