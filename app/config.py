import os

class Settings:
    PROJECT_NAME: str = "URL Shortener Service"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me_secret_key")
    
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://username:password@hostname:5432/dbname"
    )
    
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://username:password@hostname:port/0"
    )
    
    LINK_CODE_LENGTH: int = 6
    INACTIVE_DAYS: int = int(os.getenv("INACTIVE_DAYS", 30))

settings = Settings()