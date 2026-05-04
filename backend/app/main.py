
import os
from dotenv import load_dotenv

from web_server import WebServer

load_dotenv()

db_config = {
    "host":os.getenv("DB_HOST"),
    "port":os.getenv("DB_PORT"),
    "database":os.getenv("DB_NAME"),
    "user":os.getenv("DB_USER"),
    "password":os.getenv("DB_PASSWORD"),
}

if __name__ == '__main__':
    w = WebServer(db_config)

    w.run(port=8080)