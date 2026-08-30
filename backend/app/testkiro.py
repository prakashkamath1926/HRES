import os
from dotenv import load_dotenv

load_dotenv()

kiro_api_key = os.getenv("KIRO_API_KEY")

print("API key loaded:", bool(kiro_api_key))