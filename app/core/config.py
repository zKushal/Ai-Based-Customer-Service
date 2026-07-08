from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Define the variables you want to use in your app
    DATABASE_URL: str
    GROQ_API_KEY: str = None  # Added this (set to None so it doesn't crash if missing)

    # Tell Pydantic to IGNORE any other variables in .env instead of crashing
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore" 
    )

# Create a single instance of the settings
settings = Settings()