#!/bin/bash

# Reset database (useful for development)

set -e

echo "⚠️  This will delete all data in the database!"
read -p "Are you sure? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 1
fi

cd apps/api

echo "🗄️  Downgrading all migrations..."
alembic downgrade base

echo "🗄️  Running migrations..."
alembic upgrade head

echo "🌱 Seeding sample data..."
python -m app.workers.seed_data

echo "🔍 Embedding units to Qdrant..."
python -m app.workers.embed_units

echo "✅ Database reset complete!"

