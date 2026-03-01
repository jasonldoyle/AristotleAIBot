import os
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

from anthropic import Anthropic
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("plato")

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", 0))
DATABASE_URL = os.environ.get("DATABASE_URL")

# Clients
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
