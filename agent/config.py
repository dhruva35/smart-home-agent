import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    chat_model: str = os.getenv("CHAT_MODEL", "llama3-70b-8192")
    mock_api_url: str = os.getenv("MOCK_API_URL", "http://localhost:9000")


settings = Settings()
