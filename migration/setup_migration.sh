#!/bin/bash

echo "=== Setting up PostgreSQL Migration Environment ==="

# Create migration directory if it doesn't exist
mkdir -p migration

# Install required Python packages
echo "Installing required packages..."
pip install psycopg2-binary python-dotenv

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file with your database credentials"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your PostgreSQL connection string"
echo "2. Run: python migration/migrate_to_postgresql.py"
