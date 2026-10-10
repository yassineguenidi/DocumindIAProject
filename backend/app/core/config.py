from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    DATABASE_URL: str = "sqlite:///./documind.db"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    STORAGE_DIR: str = "./storage"
    GOOGLE_CLIENT_ID: str = ""
    
    # ANTHROPIC_API_KEY: str = ""
    # LLM_MODEL_FAST: str = "claude-haiku-4-5-20251001"
    # LLM_MODEL_STRONG: str = "claude-sonnet-5-5"

    LLM_PROVIDER: str = "gemini"      # gemini | ollama | anthropic
    LLM_MODEL_FAST: str = ""
    LLM_MODEL_STRONG: str = ""
    LLM_MAX_CONCURRENCY: int = 2      # appels IA simultanés (le palier gratuit est limité)
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    OLLAMA_TIMEOUT: int = 900         # un CPU peut mettre plusieurs minutes

    EMBEDDING_PROVIDER: str = ""   # vide = même fournisseur que LLM_PROVIDER ; "none" pour désactiver
    EMBEDDING_MODEL: str = ""      # gemini : gemini-embedding-001 (par défaut) ; ollama : nomic-embed-text
    
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    IMAP_FOLDER: str = "INBOX"
    IMAP_POLL_SECONDS: int = 60
    INBOX_REQUIRE_AUTH: bool = True       # exige DKIM ou SPF valide sur le mail reçu
    INBOX_MIN_IMAGE_BYTES: int = 30000    # ignore les images plus petites (logos de signature)
    
    SENSITIVE_PROVIDERS: str = ""   # ex. "ollama,anthropic" : seuls ces fournisseurs traitent les types sensibles
settings = Settings()