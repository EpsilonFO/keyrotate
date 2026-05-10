from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_password: str = "changeme"
    secret_key: str = "dev-secret-do-not-use-in-prod"
    app_base_url: str = "http://localhost:5173"
    backend_base_url: str = "http://localhost:8000"
    resend_api_key: str = ""
    resend_from: str = "KeyRotate <onboarding@resend.dev>"
    notify_email: str = ""
    slack_webhook_url: str = ""
    cron_hour: int = 9
    database_url: str = "sqlite:///./data/keyrotate.db"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
