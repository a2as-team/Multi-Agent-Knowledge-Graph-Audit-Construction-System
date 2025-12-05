# Neo4j Docker Setup Guide

This guide provides multiple ways to set up Neo4j using Docker for the Graph Construction Agent.

## 🚀 Quick Start (Recommended)

### Option 1: Using Setup Scripts

**Linux/macOS:**
```bash
chmod +x scripts/setup_neo4j.sh
./scripts/setup_neo4j.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup_neo4j.ps1
```

### Option 2: Using Docker Compose

```bash
# Edit docker-compose.yml to set your password
# Then run:
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f neo4j
```

### Option 3: Manual Docker Command

```bash
docker run -d \
    --name neo4j \
    -p 7474:7474 \
    -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    -v neo4j_import:/var/lib/neo4j/import \
    --restart unless-stopped \
    neo4j:latest
```

## 📋 Prerequisites

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Download: https://docs.docker.com/get-docker/
   - Verify: `docker --version`

2. **Docker must be running**
   - Windows/Mac: Start Docker Desktop
   - Linux: `sudo systemctl start docker`

## 🔧 Configuration

### Environment Variables

After setup, create or update your `.env` file:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

### Import Directory

CSV files should be placed in:
- **Docker volume**: `neo4j_import` (managed by Docker)
- **Local directory**: `./neo4j_import` (if using scripts)

To copy files to the Docker volume:
```bash
docker cp your_file.csv neo4j:/var/lib/neo4j/import/
```

## ✅ Verification

1. **Check container status:**
   ```bash
   docker ps | grep neo4j
   ```

2. **View logs:**
   ```bash
   docker logs neo4j
   ```

3. **Access browser UI:**
   - Open: http://localhost:7474
   - Login with: neo4j / your_password

4. **Test connection:**
   ```bash
   docker exec -it neo4j cypher-shell -u neo4j -p your_password
   ```

## 🔧 Useful Commands

```bash
# Start Neo4j
docker start neo4j
# or
docker-compose start

# Stop Neo4j
docker stop neo4j
# or
docker-compose stop

# Restart Neo4j
docker restart neo4j
# or
docker-compose restart

# View logs
docker logs neo4j
# or
docker-compose logs -f neo4j

# Access container shell
docker exec -it neo4j bash

# Remove container (keeps data volumes)
docker stop neo4j
docker rm neo4j

# Remove everything including data
docker stop neo4j
docker rm neo4j
docker volume rm neo4j_data neo4j_logs neo4j_import
```

## 🐛 Troubleshooting

### Port Already in Use

If ports 7474 or 7687 are already in use:

```bash
# Find what's using the port
# Windows:
netstat -ano | findstr :7474
netstat -ano | findstr :7687

# Linux/Mac:
lsof -i :7474
lsof -i :7687

# Change ports in docker-compose.yml or docker run command
```

### Container Won't Start

```bash
# Check logs
docker logs neo4j

# Common issues:
# - Password too simple: Use stronger password
# - Port conflict: Change ports
# - Insufficient memory: Increase Docker memory limit
```

### Can't Connect from Application

1. Verify Neo4j is running: `docker ps | grep neo4j`
2. Check environment variables in `.env`
3. Test connection: `docker exec neo4j cypher-shell -u neo4j -p password "RETURN 1"`
4. Check firewall settings

## 📚 Additional Resources

- Neo4j Documentation: https://neo4j.com/docs/
- Docker Documentation: https://docs.docker.com/
- Neo4j Docker Hub: https://hub.docker.com/_/neo4j

