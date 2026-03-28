import os
from dotenv import load_dotenv

# Load secret environment variables
load_dotenv()

class Config:
    # LLM
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")

    # Data Source APIs
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "HoloceneEvaluator/1.0")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    PRODUCT_HUNT_API_KEY = os.getenv("PRODUCT_HUNT_API_KEY", "")

    # Google Sheets Integration
    GSHEET_CREDENTIALS_JSON = os.getenv("GSHEET_CREDENTIALS_JSON", "credentials.json")
    GSHEET_NAME = os.getenv("GSHEET_NAME", "Holocene Startup Sourcing")

    # Database
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "local_json")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "holocene_sourcing")

    # Email Outreach
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    OUTREACH_EMAIL_SENDER = os.getenv("OUTREACH_EMAIL_SENDER", "Investment Interest - Holocene")

    # Investment Thesis
    THESIS = {
        "sectors": ["Blockchain", "Biotech", "Health", "Commerce", "Tech", "Space"],
        "geography": ["Europe", "North America"],
        "stage": ["Pre-seed", "Seed", "Series A"],
        "funding_range": [1000000, 10000000],  # $1M - $10M
        "linkedin_followers_max": 20000
    }
