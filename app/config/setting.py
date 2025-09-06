from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    
    groq_api_key: str
    gemini_api_key: str
    database_url: str
    port: int= 8080
    
    model_config= SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
Config= Settings()