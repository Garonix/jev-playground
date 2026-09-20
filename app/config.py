import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest")
DEFAULT_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
API_ENDPOINT = os.getenv("TYPESAFE_ENDPOINT", None)
