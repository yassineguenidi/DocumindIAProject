import imaplib
import io
import logging
import re
import threading
from email import message_from_bytes, policy
from email.utils import getaddresses, parseaddr
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal
from app.models import Company, User, UserRole
from app.services import document_service
from app.services.pipeline.runner import process_document

log = logging.getLogger(__name__)
ALLOWED_EXT = (".pdf", ".png", ".jpg", ".jpeg")
MAX_MAILS_PER_PASS = 20
_stop = threading.Event()


def enabled() -> bool:
    return bool(settings.IMAP_HOST and settings.IMAP_USER and settings.IMAP_PASSWORD and "@" in settings.IMAP_USER)


def address_for(token: str) -> Optional[str]:
    if not enabled():
        return None
    local, domain = settings.IMAP_USER.split("@", 1)
    return f"{local}+{token}@{domain}"


def _token_from(msg) -> Optional[str]:
    local, _, domain = settings.IMAP_USER.lower().partition("@")
    pattern = re.compile(rf"^{re.escape(local)}\+([a-z0-9]+)@{re.escape(domain)}$")
    headers: List[str] = []
    for h in ("To", "Cc", "Delivered-To", "X-Original-To", "X-Forwarded-To"):
        headers += [str(v) for v in msg.get_all(h, [])]
    for _, addr in getaddresses(headers):
        m = pattern.match(addr.strip().lower())
        if m:
            return m.group(1)
    return None


def _authenticated(msg) -> bool:
    if not settings.INBOX_REQUIRE_AUTH:
        return True
    results = " ".join(str(v) for v in msg.get_all("Authentication-Results", [])).lower()
    return "dkim=pass" in results or "spf=pass" in results


def _sender_allowed(db: Session, company: Company, sender: str) -> bool:
    rules = [r for r in re.split(r"[,;\s]+", (company.inbox_allowed or "").lower()) if r]
    if any(sender == r or (r.startswith("@") and sender.endswith(r)) for r in rules):
        return True
    return db.query(User).filter(
        User.company_id == company.id, User.email == sender, User.is_active.is_(True)
    ).first() is not None


def _attachments(msg) -> List[Tuple[str, bytes]]:
    out = []
    for part in msg.iter_attachments():
        name = part.get_filename() or ""
        ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in ALLOWED_EXT:
            continue
        try:
            data = part.get_content()
        except Exception:
            continue
        if not isinstance(data, (bytes, bytearray)):
            continue
        if ext != ".pdf" and (part.get_content_disposition() == "inline" or len(data) < settings.INBOX_MIN_IMAGE_BYTES):
            continue  # logo de signature, pas un document
        out.append((name, bytes(data)))
    return out


def _handle(raw: bytes) -> None:
    msg = message_from_bytes(raw, policy=policy.default)
    sender = parseaddr(str(msg.get("From", "")))[1].lower()
    token = _token_from(msg)
    if not token:
        log.info("Email de %s ignoré : adresse sans jeton", sender)
        return

    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.inbox_token == token).first()
        if company is None:
            log.info("Email de %s ignoré : jeton inconnu", sender)
            return
        if not _authenticated(msg):
            log.warning("Email de %s ignoré : expéditeur non authentifié (DKIM/SPF)", sender)
            return
        if not _sender_allowed(db, company, sender):
            log.warning("Email de %s ignoré : expéditeur non autorisé pour l'entreprise %s", sender, company.id)
            return
        admin = db.query(User).filter(
            User.company_id == company.id, User.role == UserRole.ADMIN, User.is_active.is_(True)
        ).order_by(User.id).first()
        if admin is None:
            return

        created = []
        for name, data in _attachments(msg):
            try:
                created.append(document_service.ingest(db, admin, name, io.BytesIO(data)))
            except HTTPException as exc:
                log.warning("Pièce jointe « %s » refusée : %s", name, exc.detail)
        log.info("Email de %s : %d document(s) créé(s) pour l'entreprise %s", sender, len(created), company.id)
        for doc in created:
            process_document(doc.id)  # séquentiel : respecte les limites du palier gratuit
    finally:
        db.close()


def _poll_once() -> None:
    conn = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
    try:
        conn.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        conn.select(settings.IMAP_FOLDER)
        typ, data = conn.search(None, "UNSEEN")
        ids = data[0].split() if typ == "OK" and data and data[0] else []
        for num in ids[:MAX_MAILS_PER_PASS]:
            typ, fetched = conn.fetch(num, "(RFC822)")  # marque le message comme lu
            if typ != "OK" or not fetched or not isinstance(fetched[0], tuple):
                continue
            try:
                _handle(fetched[0][1])
            except Exception:
                log.exception("Email %s non traité", num)
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def _loop() -> None:
    while not _stop.is_set():
        try:
            _poll_once()
        except Exception:
            log.exception("Relève de la boîte mail impossible")
        _stop.wait(settings.IMAP_POLL_SECONDS)


def start() -> None:
    if enabled():
        threading.Thread(target=_loop, daemon=True, name="email-intake").start()
        log.info("Réception par email activée (%s)", settings.IMAP_USER)


def stop() -> None:
    _stop.set()