from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    JWT_SECRET: str  
    JWT_ALGORITHM: str = "HS256" # Standard JWT algorithm

    class Config:
        env_file = ".env"

settings = Settings()