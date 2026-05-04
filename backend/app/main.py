
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    "host":os.getenv("DB_HOST"),
    "port":os.getenv("DB_PORT"),
    "database":os.getenv("DB_NAME"),
    "user":os.getenv("DB_USER"),
    "password":os.getenv("DB_PASSWORD"),
}

print(db_config)