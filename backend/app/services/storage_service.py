import uuid
from pathlib import Path
from typing import BinaryIO, Tuple

from app.core.config import settings

CHUNK = 1024 * 1024  # 1 Mo


class FileTooLarge(Exception):
    pass


class LocalStorage:
    """Stockage sur disque. Les fichiers sont rangés par entreprise, avec un nom
    généré (uuid) : le nom d'origine de l'utilisateur n'est jamais utilisé comme chemin."""

    def __init__(self, base_dir: str):
        self.base = Path(base_dir).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.base / key).resolve()
        if self.base not in path.parents:  # protection contre ../
            raise ValueError("Clé de stockage invalide")
        return path

    def save(self, company_id: int, extension: str, stream: BinaryIO, max_bytes: int) -> Tuple[str, int]:
        key = f"{company_id}/{uuid.uuid4().hex}{extension}"
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        try:
            with open(path, "wb") as out:
                while True:
                    chunk = stream.read(CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise FileTooLarge()
                    out.write(chunk)
        except Exception:
            path.unlink(missing_ok=True)  # pas de fichier partiel
            raise
        return key, size

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def open_path(self, key: str) -> Path:
        return self._path(key)


storage = LocalStorage(settings.STORAGE_DIR)