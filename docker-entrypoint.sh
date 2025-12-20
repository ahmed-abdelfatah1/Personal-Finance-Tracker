#!/bin/bash
set -e

echo "Initializing database..."
python -c "from src.app import create_app; from src.app.db import init_db; app = create_app(); app.app_context().push(); init_db()"

echo "Starting application..."
exec "$@"

