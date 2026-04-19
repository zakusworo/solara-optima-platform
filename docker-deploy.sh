#!/bin/bash
# Docker deployment script for Solar UC/ED Platform

set -e

echo "=========================================="
echo "Solar UC/ED Platform - Docker Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: docker-compose not found, trying 'docker compose'...${NC}"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}Docker version:${NC} $(docker --version)"
echo ""

# Parse arguments
ACTION=${1:-"up"}

case $ACTION in
    "up")
        echo -e "${YELLOW}Starting all services...${NC}"
        $COMPOSE_CMD up -d --build
        echo ""
        echo -e "${GREEN}✓ Services started!${NC}"
        echo ""
        echo "Access the platform:"
        echo "  Frontend:  http://localhost:3000"
        echo "  Backend:   http://localhost:8000"
        echo "  API Docs:  http://localhost:8000/docs"
        echo ""
        echo "View logs:"
        echo "  $COMPOSE_CMD logs -f"
        echo ""
        ;;
    
    "down")
        echo -e "${YELLOW}Stopping all services...${NC}"
        $COMPOSE_CMD down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;
    
    "restart")
        echo -e "${YELLOW}Restarting services...${NC}"
        $COMPOSE_CMD restart
        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;
    
    "logs")
        $COMPOSE_CMD logs -f ${2:-""}
        ;;
    
    "build")
        echo -e "${YELLOW}Building containers...${NC}"
        $COMPOSE_CMD build --no-cache
        echo -e "${GREEN}✓ Build complete${NC}"
        ;;
    
    "status")
        echo -e "${YELLOW}Service Status:${NC}"
        $COMPOSE_CMD ps
        ;;
    
    "ollama-pull")
        MODEL=${2:-"llama3.2"}
        echo -e "${YELLOW}Pulling Ollama model: $MODEL${NC}"
        docker exec solar-uc-ed-ollama ollama pull $MODEL
        echo -e "${GREEN}✓ Model pulled${NC}"
        ;;
    
    "clean")
        echo -e "${YELLOW}Cleaning up Docker resources...${NC}"
        $COMPOSE_CMD down -v
        docker system prune -f
        echo -e "${GREEN}✓ Cleanup complete${NC}"
        ;;
    
    *)
        echo "Usage: ./docker-deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  up            Start all services (default)"
        echo "  down          Stop all services"
        echo "  restart       Restart services"
        echo "  logs [svc]    View logs (optionally filter by service)"
        echo "  build         Rebuild containers"
        echo "  status        Show service status"
        echo "  ollama-pull   Pull Ollama model (default: llama3.2)"
        echo "  clean         Remove containers and volumes"
        echo ""
        ;;
esac

echo "=========================================="
