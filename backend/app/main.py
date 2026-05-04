
import os
from dotenv import load_dotenv

from web_server import WebServer

load_dotenv()

import os
from web_server import WebServer

db_config = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Instantiate the server
ws = WebServer(db_config)

# Gunicorn needs to point to this 'app' object
app = ws.app 

if __name__ == "__main__":
    # This block only runs if you call 'python main.py' manually
    ws.run(host='0.0.0.0', port=8080)