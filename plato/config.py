import os
import logging
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client
from anthropic import Anthropic

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("plato")

# Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", 0))

# Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)