import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    chat_model: str = os.getenv("CHAT_MODEL", "gemini-3.1-flash-lite")
    mock_api_url: str = os.getenv("MOCK_API_URL", "http://localhost:9000")


settings = Settings()
