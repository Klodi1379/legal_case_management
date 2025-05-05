import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== DEBUG SETTINGS ===")
print(f"DEBUG: {os.getenv('DEBUG')}")
print(f"DEBUG value equals 'True': {os.getenv('DEBUG') == 'True'}")
print(f"DEBUG is True: {os.getenv('DEBUG', 'True') == 'True'}")
print(f"ALLOWED_HOSTS: {os.getenv('ALLOWED_HOSTS')}")
print(f"ALLOWED_HOSTS split: {os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')}")
print("===================")
