#!/bin/bash
# Docker run script for Personal Finance Tracker

# Create a named volume for database persistence (if it doesn't exist)
docker volume create finance_data 2>/dev/null || true

# Run the container
docker run -d \
  --name finance-tracker \
  -p 5000:5000 \
  -v finance_data:/app/data \
  --restart unless-stopped \
  finance-app:latest

echo "Container 'finance-tracker' started!"
echo "Access the application at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  View logs: docker logs finance-tracker"
echo "  Stop: docker stop finance-tracker"
echo "  Start: docker start finance-tracker"
echo "  Remove: docker rm -f finance-tracker"

