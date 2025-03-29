import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("SERVER_HOST", "0.0.0.0")
port = os.getenv("SERVER_PORT", "8001")

os.system(f"python manage.py runserver {host}:{port}")
