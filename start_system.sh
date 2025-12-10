#!/bin/bash

echo "🚗 Iniciando Sistema de Estacionamento Inteligente com MQTT"
echo "================================================"

# Verificar se o Mosquitto está rodando
echo "📡 Verificando broker MQTT..."
if systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto está ativo"
else
    echo "❌ Mosquitto não está ativo. Inicie com: sudo systemctl start mosquitto"
    exit 1
fi

# Iniciar backend com MQTT em background silencioso
echo "🎥 Iniciando backend de detecção com MQTT..."
python3 main_mqtt.py > /dev/null 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Esperar um pouco para o backend iniciar
sleep 3

# Iniciar frontend web em background silencioso
echo "🌐 Iniciando frontend web..."
python3 app.py > /dev/null 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "🎉 Sistema iniciado com sucesso!"
echo "================================="
echo "📹 Backend de detecção: Rodando (PID: $BACKEND_PID)"
echo "🌐 Frontend web: http://localhost:5000"
echo "📡 MQTT Broker: localhost:1883"
echo ""
echo "📝 Logs silenciados. Para ver logs, execute:"
echo "   tail -f /tmp/mqtt_backend.log  (se desejar ativar logs)"
echo ""
echo "Pressione Ctrl+C para parar o sistema"
echo ""

# Aguardar interrupção
trap 'echo "🛑 Parando sistema..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ Sistema parado"; exit' INT

# Manter script rodando sem mostrar output
while true; do
    sleep 1
done