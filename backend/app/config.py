from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    MONGODB_URL: str = Field(default="mongodb://mongo:27017")
    MONGODB_DB_NAME: str = Field(default="merchant_ai")
    REDIS_URL: str = Field(default="redis://redis:6379")

    RAZORPAY_KEY_ID: str = Field(default="")
    RAZORPAY_KEY_SECRET: str = Field(default="")
    RAZORPAY_WEBHOOK_SECRET: str = Field(default="")
    JWT_SECRET: str = Field(default="")
    ENCRYPTION_KEY: str = Field(default="")
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000")

    OPENAI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
