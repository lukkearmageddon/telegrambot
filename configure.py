from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: SecretStr
    payment_provider_token: SecretStr
    stripe_api_key: SecretStr
    webhook_secret: SecretStr
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()
