#!/bin/bash

set -e

echo "🚀 Starting deployment..."

cd "$(dirname "$0")"

echo "📦 Loading environment file..."
cp ~/beiroes_configs/.env .env

set -o allexport
source .env
set +o allexport

echo "🐳 Starting database..."
docker-compose up -d db

echo "⏳ Waiting for database..."
until docker exec beiroes_db pg_isready -U "$DB_USER" > /dev/null 2>&1; do
  sleep 2
done

echo "🐍 Creating virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt

echo "🧪 Running tests..."
export DB_NAME=beiroes_test
export PYTHONPATH=$(pwd)/backend/app

cd backend/app
../../.venv/bin/python3 auto_test_all.py
cd ../../

echo "🐳 Deploying application..."
export DB_NAME=caderno_quim

docker-compose --env-file .env up -d --build

echo "🌱 Seeding database..."
cd backend/app
../../.venv/bin/python3 populate_database.py
cd ../../

echo "✅ Deployment completed!"

# #!/bin/bash

# set -e

# echo "🚀 Starting Beiroes deployment..."

# cd "$(dirname "$0")"

# echo "📦 Linking environment file..."
# ln -sf ~/beiroes_configs/.env .env

# echo "🔐 Loading environment variables..."
# set -o allexport
# source .env
# set +o allexport

# echo "🐍 Setting up Python virtual environment..."
# if [ ! -d ".venv" ]; then
#   python3 -m venv .venv
# fi

# source .venv/bin/activate

# echo "⬆️ Upgrading pip..."
# pip install --upgrade pip

# echo "📚 Installing dependencies..."
# pip install -r backend/requirements.txt

# echo "🐳 Starting database..."
# docker-compose up -d db

# echo "⏳ Waiting for database to be ready..."
# # sleep 7
# until docker inspect --format='{{json .State.Health.Status}}' beiroes_db | grep healthy; do
#   sleep 2
# done

# echo "🧪 Running tests..."
# export DB_NAME=beiroes_test

# cd backend/app
# ../../.venv/bin/python3 auto_test_all.py
# cd ../../

# echo "🐳 Building and starting services..."
# export DB_NAME=caderno_quim
# docker-compose --env-file .env up -d --build

# echo "🌱 Seeding database..."
# #export DB_HOST=db
# #export DB_PORT=5432
# #export DB_USER=beiroes_admin
# #export DB_NAME=caderno_quim
# #export PYTHONPATH=$(pwd)/backend/app

# source .env

# cd backend/app
# ../../.venv/bin/python3 populate_database.py
# cd ../../

# echo "✅ Deployment finished successfully!"
