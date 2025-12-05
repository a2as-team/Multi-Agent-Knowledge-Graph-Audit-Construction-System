# Neo4j Docker Setup Script for Windows PowerShell
# This script sets up Neo4j using Docker for easy installation and management

Write-Host "🚀 Neo4j Docker Setup" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed." -ForegroundColor Red
    Write-Host "   Please install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running." -ForegroundColor Red
    Write-Host "   Please start Docker Desktop." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Get password from user or use default
$NEO4J_PASSWORD = Read-Host "Enter Neo4j password (default: neo4j)"
if ([string]::IsNullOrWhiteSpace($NEO4J_PASSWORD)) {
    $NEO4J_PASSWORD = "neo4j"
}

Write-Host ""
Write-Host "📦 Setting up Neo4j container..." -ForegroundColor Cyan

# Stop and remove existing container if it exists
$existingContainer = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^neo4j$"
if ($existingContainer) {
    Write-Host "   Stopping existing Neo4j container..." -ForegroundColor Yellow
    docker stop neo4j 2>$null
    docker rm neo4j 2>$null
}

# Create import directory if it doesn't exist
$IMPORT_DIR = ".\neo4j_import"
if (-not (Test-Path $IMPORT_DIR)) {
    New-Item -ItemType Directory -Path $IMPORT_DIR | Out-Null
}
Write-Host "   Created import directory: $IMPORT_DIR" -ForegroundColor Green

# Run Neo4j container
Write-Host "   Starting Neo4j container..." -ForegroundColor Cyan
docker run -d `
    --name neo4j `
    -p 7474:7474 `
    -p 7687:7687 `
    -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD `
    -e NEO4J_PLUGINS='["apoc"]' `
    -e NEO4J_dbms_security_procedures_unrestricted=apoc.* `
    -v neo4j_data:/data `
    -v neo4j_logs:/logs `
    -v neo4j_import:/var/lib/neo4j/import `
    --restart unless-stopped `
    neo4j:latest

Write-Host ""
Write-Host "⏳ Waiting for Neo4j to start (this may take 10-20 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Wait for Neo4j to be ready
$MAX_ATTEMPTS = 30
$ATTEMPT = 0
$READY = $false

while ($ATTEMPT -lt $MAX_ATTEMPTS) {
    try {
        docker exec neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1" 2>$null | Out-Null
        Write-Host "✅ Neo4j is ready!" -ForegroundColor Green
        $READY = $true
        break
    } catch {
        $ATTEMPT++
        Write-Host "   Waiting... ($ATTEMPT/$MAX_ATTEMPTS)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $READY) {
    Write-Host "⚠️  Neo4j is starting but not fully ready yet." -ForegroundColor Yellow
    Write-Host "   Check status with: docker logs neo4j" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Neo4j Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Browser UI: http://localhost:7474" -ForegroundColor Cyan
Write-Host "🔌 Bolt URI: bolt://localhost:7687" -ForegroundColor Cyan
Write-Host "👤 Username: neo4j" -ForegroundColor Cyan
Write-Host "🔑 Password: $NEO4J_PASSWORD" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Import Directory: $IMPORT_DIR" -ForegroundColor Cyan
Write-Host "   Place your CSV files here for loading" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Environment Variables for .env file:" -ForegroundColor Cyan
Write-Host "   NEO4J_URI=bolt://localhost:7687" -ForegroundColor Gray
Write-Host "   NEO4J_USERNAME=neo4j" -ForegroundColor Gray
Write-Host "   NEO4J_PASSWORD=$NEO4J_PASSWORD" -ForegroundColor Gray
Write-Host "   NEO4J_DATABASE=neo4j" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "   docker logs neo4j          # View logs" -ForegroundColor Gray
Write-Host "   docker stop neo4j          # Stop Neo4j" -ForegroundColor Gray
Write-Host "   docker start neo4j         # Start Neo4j" -ForegroundColor Gray
Write-Host "   docker restart neo4j       # Restart Neo4j" -ForegroundColor Gray
Write-Host "   docker exec -it neo4j bash # Access container shell" -ForegroundColor Gray
Write-Host ""

