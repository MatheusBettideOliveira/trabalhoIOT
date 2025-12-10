#!/bin/bash

echo "🚀 QUICK START - Sistema de Estacionamento IoT"
echo "=============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Verificando Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado. Instale Python 3.8+${NC}"
    exit 1
else
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✅ Python $PYTHON_VERSION encontrado${NC}"
fi

echo -e "${BLUE}2. Verificando Mosquitto...${NC}"
if ! command -v mosquitto &> /dev/null; then
    echo -e "${RED}❌ Mosquitto não encontrado${NC}"
    echo -e "${YELLOW}📥 Instalando Mosquitto...${NC}"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y mosquitto mosquitto-clients
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install mosquitto
    else
        echo -e "${RED}❌ Sistema não suportado automaticamente. Instale Mosquitto manualmente${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Mosquitto encontrado${NC}"
fi

echo -e "${BLUE}3. Verificando arquivo de posições...${NC}"
if [ ! -f "CarParkPos" ]; then
    echo -e "${YELLOW}⚠️  Arquivo CarParkPos não encontrado${NC}"
    echo -e "${YELLOW}📝 Execute 'python3 ParkingSpacePicker.py' para configurar as vagas${NC}"

    # Criar arquivo vazio para não dar erro
    python3 -c "
import pickle
pickle.dump([], open('CarParkPos', 'wb'))
print('Arquivo CarParkPos criado (vazio)')
"
fi

echo -e "${BLUE}4. Instalando dependências Python...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo -e "${YELLOW}⚠️  requirements.txt não encontrado, instalando manualmente${NC}"
    pip3 install opencv-python cvzone plyer paho-mqtt flask numpy
fi

echo -e "${BLUE}5. Iniciando Mosquitto...${NC}"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start mosquitto 2>/dev/null || echo "Mosquitto já rodando"
    sudo systemctl enable mosquitto 2>/dev/null
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start mosquitto 2>/dev/null || echo "Mosquitto já rodando"
fi

echo ""
echo -e "${GREEN}🎉 Sistema pronto para uso!${NC}"
echo "=============================================="
echo -e "${BLUE}📋 Próximos passos:${NC}"
echo ""
echo "1. ${YELLOW}Configurar as vagas (se necessário):${NC}"
echo "   python3 ParkingSpacePicker.py"
echo ""
echo "2. ${YELLOW}Iniciar o sistema:${NC}"
echo "   ./start_system.sh"
echo ""
echo "3. ${YELLOW}Acessar o frontend:${NC}"
echo "   http://localhost:5000"
echo ""
echo -e "${GREEN}✅ Deploy completo!${NC}"