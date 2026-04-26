#!/bin/bash

# Script para levantar frontend y backend simultáneamente

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT"

echo "🚀 Iniciando Football Motor (Frontend + Backend)..."
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${BLUE}Deteniendo servidores...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}✓ Servidores detenidos${NC}"
}

trap cleanup EXIT INT TERM

# Levantar Backend (FastAPI)
echo -e "${BLUE}📦 Backend (FastAPI en puerto 8000)...${NC}"
cd "$BACKEND_DIR"
python -m uvicorn src.motor_futbol.api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 2

# Levantar Frontend (Vite en puerto 5173)
echo -e "${BLUE}⚛️  Frontend (React + Vite en puerto 5173)...${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✓ Ambos servidores iniciados${NC}"
echo -e "${GREEN}  Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  Backend:  http://localhost:8000${NC}"
echo ""
echo -e "${BLUE}Presiona Ctrl+C para detener${NC}"
echo ""

# Mantener el script corriendo
wait
