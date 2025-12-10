from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import json
import threading
import time

app = Flask(__name__)

# Configuração MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_STATUS = "parking/status"
MQTT_TOPIC_SPOT = "parking/spot"
MQTT_TOPIC_UPDATE = "parking/update"

# Armazenamento de dados
parking_data = {
    "total_spots": 0,
    "free_spots": 0,
    "occupied_spots": 0,
    "spots": {},
    "last_update": None
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Frontend MQTT conectado com sucesso!")
        # Inscrever nos tópicos
        client.subscribe(MQTT_TOPIC_STATUS)
        client.subscribe(f"{MQTT_TOPIC_SPOT}/+")
        client.subscribe(MQTT_TOPIC_UPDATE)
    else:
        print(f"Falha na conexão MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    global parking_data

    try:
        payload = json.loads(msg.payload.decode())

        if msg.topic == MQTT_TOPIC_STATUS:
            # Atualizar status geral
            parking_data.update(payload)
            parking_data["last_update"] = time.time()
            print(f"Status atualizado: {payload['free_spots']}/{payload['total_spots']} vagas livres")

        elif msg.topic.startswith(MQTT_TOPIC_SPOT):
            # Atualizar status individual da vaga
            spot_id = msg.topic.split('/')[-1]
            parking_data["spots"][spot_id] = payload
            parking_data["last_update"] = time.time()

        elif msg.topic == MQTT_TOPIC_UPDATE:
            # Atualização completa
            parking_data["total_spots"] = payload["general"]["total_spots"]
            parking_data["free_spots"] = payload["general"]["free_spots"]
            parking_data["occupied_spots"] = payload["general"]["occupied_spots"]
            parking_data["spots"] = payload["spots"]
            parking_data["last_update"] = time.time()
            print(f"Update completo: {payload['general']['free_spots']}/{payload['general']['total_spots']} vagas livres")

    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")

def mqtt_thread():
    """Thread para manter conexão MQTT ativa"""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Erro na conexão MQTT: {e}")

# Iniciar thread MQTT em background
mqtt_client_thread = threading.Thread(target=mqtt_thread, daemon=True)
mqtt_client_thread.start()

@app.route('/')
def index():
    """Página principal do frontend"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """API endpoint para status atual do estacionamento"""
    return jsonify(parking_data)

@app.route('/api/spots')
def get_spots():
    """API endpoint para status individual das vagas"""
    return jsonify(parking_data["spots"])

if __name__ == '__main__':
    print("Iniciando servidor web do estacionamento...")
    print("Acesse: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)