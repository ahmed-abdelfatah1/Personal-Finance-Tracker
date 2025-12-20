# Docker Container Run Commands

## Option 1: Using Docker Desktop GUI

1. Open Docker Desktop
2. Go to **Images** tab
3. Find your image (e.g., `finance-app:latest`)
4. Click the **Run** button (play icon)
5. In the run options:
   - **Container name**: `finance-tracker`
   - **Ports**: Map `5000:5000` (Host: 5000 → Container: 5000)
   - **Volumes**: Click "Volumes" tab → Add volume:
     - **Host path**: (leave empty or create a local folder)
     - **Container path**: `/app/data`
     - Or use a named volume: `finance_data:/app/data`
   - **Restart policy**: `Unless stopped`
6. Click **Run**

## Option 2: Using Command Line

### Basic Run (without persistence)
```bash
docker run -d --name finance-tracker -p 5000:5000 finance-app:latest
```

### Run with Database Persistence (Recommended)
```bash
# Create a named volume for database
docker volume create finance_data

# Run container with volume
docker run -d \
  --name finance-tracker \
  -p 5000:5000 \
  -v finance_data:/app/data \
  --restart unless-stopped \
  finance-app:latest
```

### Run with Local Directory Mount (Alternative)
```bash
# Create local directory
mkdir -p ./docker-data

# Run container with local directory mount
docker run -d \
  --name finance-tracker \
  -p 5000:5000 \
  -v "$(pwd)/docker-data:/app/data" \
  --restart unless-stopped \
  finance-app:latest
```

## Useful Commands

```bash
# View container logs
docker logs finance-tracker

# View live logs
docker logs -f finance-tracker

# Stop container
docker stop finance-tracker

# Start stopped container
docker start finance-tracker

# Restart container
docker restart finance-tracker

# Remove container
docker rm -f finance-tracker

# Access container shell
docker exec -it finance-tracker /bin/bash

# View container status
docker ps -a | grep finance-tracker
```

## Access the Application

Once running, access at: **http://localhost:5000**

