#!/bin/bash

echo "🚗 Iniciando Sistema de Estacionamento Inteligente com MQTT (Verbose)"
echo "=================================================================="

# Verificar se o Mosquitto está rodando
echo "📡 Verificando broker MQTT..."
if systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto está ativo"
else
    echo "❌ Mosquitto não está ativo. Inicie com: sudo systemctl start mosquitto"
    exit 1
fi

# Criar diretório de logs
mkdir -p logs

# Iniciar backend com MQTT e salvar logs
echo "🎥 Iniciando backend de detecção com MQTT..."
python3 main_mqtt.py 2>&1 | tee logs/backend.log &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID (logs em logs/backend.log)"

# Esperar um pouco para o backend iniciar
sleep 3

# Iniciar frontend web e salvar logs
echo "🌐 Iniciando frontend web..."
python3 app.py 2>&1 | tee logs/frontend.log &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID (logs em logs/frontend.log)"

echo ""
echo "🎉 Sistema iniciado com sucesso!"
echo "================================="
echo "📹 Backend de detecção: Rodando (PID: $BACKEND_PID)"
echo "🌐 Frontend web: http://localhost:5000"
echo "📡 MQTT Broker: localhost:1883"
echo "📁 Logs disponíveis em:"
echo "   - Backend: logs/backend.log"
echo "   - Frontend: logs/frontend.log"
echo ""
echo "Pressione Ctrl+C para parar o sistema"
echo ""

# Aguardar interrupção
trap 'echo "🛑 Parando sistema..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ Sistema parado"; echo "📝 Logs salvos em logs/"; exit' INT

# Manter script rodando
wait