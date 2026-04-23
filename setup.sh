#!/bin/bash
# Solara Optima Platform - Setup Script
# Automated installation for Bandung development environment

set -e

echo "=========================================="
echo "Solara Optima Platform - Setup"
echo "Politeknik Energi dan Pertambangan Bandung"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
python3 --version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.10+ is required"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}[2/6] Setting up Python virtual environment...${NC}"
cd backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
fi

cd ..

# Check Node.js
echo -e "${YELLOW}[4/6] Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js not found. Frontend setup skipped."
    echo "Install Node.js 18+ from https://nodejs.org/"
else
    node --version
    
    # Install frontend dependencies
    echo -e "${YELLOW}[5/6] Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Check Ollama
echo -e "${YELLOW}[6/6] Checking Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "Warning: Ollama not found. AI forecasting will be unavailable."
    echo "Install from https://ollama.ai/"
else
    ollama --version
    
    # Pull models if not present
    echo "Pulling AI models for forecasting..."
    ollama pull qwen3.5 || echo "Model pull failed, will retry later"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "To start the platform:"
echo ""
echo "1. Backend (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Access the platform:"
echo "   http://localhost:3000"
echo ""
echo "API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "=========================================="
