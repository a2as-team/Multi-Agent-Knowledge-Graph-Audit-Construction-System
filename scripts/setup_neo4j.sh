#!/bin/bash
# Neo4j Docker Setup Script for Linux/macOS
# This script sets up Neo4j using Docker for easy installation and management

set -e  # Exit on error

echo "🚀 Neo4j Docker Setup"
echo "===================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "   Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    echo "   Please start Docker Desktop or Docker daemon."
    exit 1
fi

echo "✅ Docker is installed and running"
echo ""

# Get password from user or use default
read -p "Enter Neo4j password (default: neo4j): " NEO4J_PASSWORD
NEO4J_PASSWORD=${NEO4J_PASSWORD:-neo4j}

echo ""
echo "📦 Setting up Neo4j container..."

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^neo4j$"; then
    echo "   Stopping existing Neo4j container..."
    docker stop neo4j 2>/dev/null || true
    docker rm neo4j 2>/dev/null || true
fi

# Create import directory if it doesn't exist
IMPORT_DIR="./neo4j_import"
mkdir -p "$IMPORT_DIR"
echo "   Created import directory: $IMPORT_DIR"

# Run Neo4j container
echo "   Starting Neo4j container..."
docker run -d \
    --name neo4j \
    -p 7474:7474 \
    -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD \
    -e NEO4J_PLUGINS='["apoc"]' \
    -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    -v neo4j_import:/var/lib/neo4j/import \
    --restart unless-stopped \
    neo4j:latest

echo ""
echo "⏳ Waiting for Neo4j to start (this may take 10-20 seconds)..."
sleep 5

# Wait for Neo4j to be ready
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" &> /dev/null; then
        echo "✅ Neo4j is ready!"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "⚠️  Neo4j is starting but not fully ready yet."
    echo "   Check status with: docker logs neo4j"
fi

echo ""
echo "=========================================="
echo "✅ Neo4j Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Browser UI: http://localhost:7474"
echo "🔌 Bolt URI: bolt://localhost:7687"
echo "👤 Username: neo4j"
echo "🔑 Password: $NEO4J_PASSWORD"
echo ""
echo "📁 Import Directory: $IMPORT_DIR"
echo "   Place your CSV files here for loading"
echo ""
echo "📝 Environment Variables for .env file:"
echo "   NEO4J_URI=bolt://localhost:7687"
echo "   NEO4J_USERNAME=neo4j"
echo "   NEO4J_PASSWORD=$NEO4J_PASSWORD"
echo "   NEO4J_DATABASE=neo4j"
echo ""
echo "🔧 Useful Commands:"
echo "   docker logs neo4j          # View logs"
echo "   docker stop neo4j          # Stop Neo4j"
echo "   docker start neo4j         # Start Neo4j"
echo "   docker restart neo4j       # Restart Neo4j"
echo "   docker exec -it neo4j bash # Access container shell"
echo ""

