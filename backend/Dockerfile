FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema para o psycopg2 (Postgres)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["python3","test_u_dao.py"]
