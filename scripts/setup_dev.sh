#!/bin/bash

# Development setup script

set -e

echo "🚀 Setting up Real Estate AI CRM..."

# Create .env files if they don't exist
if [ ! -f apps/api/.env ]; then
    echo "📝 Creating API .env file..."
    cp apps/api/.env.example apps/api/.env
    echo "⚠️  Remember to add your OPENAI_API_KEY to apps/api/.env"
fi

if [ ! -f apps/web/.env ]; then
    echo "📝 Creating Web .env file..."
    cp apps/web/.env.example apps/web/.env
fi

# Start infrastructure services
echo "🐳 Starting infrastructure services (Postgres, Qdrant, Redis)..."
cd infra
docker-compose -f docker-compose.dev.yml up -d postgres qdrant redis

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

cd ..

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd apps/api
pip install -r requirements.txt

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Seed data
echo "🌱 Seeding sample data..."
python -m app.workers.seed_data

# Embed units
echo "🔍 Embedding units to Qdrant..."
python -m app.workers.embed_units

cd ../..

# Install Node dependencies
echo "📦 Installing Node dependencies..."
cd apps/web
npm install

cd ../..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your OPENAI_API_KEY to apps/api/.env"
echo "2. Start the API: cd apps/api && uvicorn app.main:app --reload"
echo "3. Start the Web: cd apps/web && npm run dev"
echo ""
echo "Or use Docker Compose to run everything:"
echo "  cd infra && docker-compose -f docker-compose.dev.yml up"

