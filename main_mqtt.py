import cv2
import pickle
import cvzone
import numpy as np
import json
import paho.mqtt.client as mqtt
import time


MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_STATUS = "parking/status"
MQTT_TOPIC_SPOT = "parking/spot"
MQTT_TOPIC_UPDATE = "parking/update"


cap = cv2.VideoCapture('carPark.mp4')


with open('CarParkPos', 'rb') as f:
    poslist = pickle.load(f)
    width, height = 107, 48


previous_status = {}
last_update_time = 0
last_console_log = 0


spot_stability = {}  
STABILITY_THRESHOLD = 5  
CONFIRMATION_COUNT = 10   


VIDEO_SPEED = 0.5  
PAUSE_BETWEEN_FRAMES = 30  

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao MQTT Broker com sucesso!")
    else:
        print(f"Falha na conexão com MQTT Broker. Código: {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Desconectado do MQTT Broker. Tentando reconectar...")
        client.reconnect()


client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"Erro ao conectar ao MQTT Broker: {e}")
    client = None

def checkParkingSpace(imgPro):
    global previous_status, last_update_time, last_console_log, spot_stability

    spaceCounter = 0
    current_status = {}

    for i, pos in enumerate(poslist):
        x, y = pos
        imgCrop = imgPro[y:y+height, x:x+width]
        count = cv2.countNonZero(imgCrop)
        
        is_occupied = count >= 950
        spot_id = f"spot_{i:02d}"

        
        if spot_id not in spot_stability:
            spot_stability[spot_id] = {
                "occupied_count": 0,
                "free_count": 0,
                "stable_status": "unknown"
            }
        else:
            
            if is_occupied:
                spot_stability[spot_id]["occupied_count"] += 1
                spot_stability[spot_id]["free_count"] = 0
            else:
                spot_stability[spot_id]["free_count"] += 1
                spot_stability[spot_id]["occupied_count"] = 0

            
            if spot_stability[spot_id]["occupied_count"] >= CONFIRMATION_COUNT:
                spot_stability[spot_id]["stable_status"] = "occupied"
            elif spot_stability[spot_id]["free_count"] >= CONFIRMATION_COUNT:
                spot_stability[spot_id]["stable_status"] = "free"

        
        stable_status = spot_stability[spot_id]["stable_status"]
        if stable_status == "unknown" and spot_id in previous_status:
            stable_status = previous_status[spot_id]["status"]

        
        if stable_status == "free":
            color = (0, 255, 0)  
            thickness = 5
            spaceCounter += 1
            current_status[spot_id] = {"status": "free", "count": count}
        elif stable_status == "occupied":
            color = (0, 0, 255)  
            thickness = 2
            current_status[spot_id] = {"status": "occupied", "count": count}
        else:
            
            color = (255, 255, 0)  
            thickness = 3
            if spot_id in previous_status:
                current_status[spot_id] = previous_status[spot_id]
            else:
                current_status[spot_id] = {"status": "unknown", "count": count}

        
        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)

    
    current_time = time.time()

    
    significant_change = False
    changed_spots = 0

    for spot_id, current_data in current_status.items():
        if spot_id in previous_status:
            if current_data["status"] != previous_status[spot_id]["status"]:
                changed_spots += 1
        else:
            
            previous_status[spot_id] = current_data

    
    significant_change = changed_spots > 2

    
    if significant_change and current_time - last_console_log > 5:
        print(f"MQTT: {changed_spots} vagas mudaram, publicando update...")
        last_console_log = current_time

    if (significant_change or current_time - last_update_time > 2):

        if client:
            try:
                
                complete_update = {
                    "total_spots": len(poslist),
                    "free_spots": spaceCounter,
                    "occupied_spots": len(poslist) - spaceCounter,
                    "spots": current_status,
                    "timestamp": time.time()
                }
                client.publish(MQTT_TOPIC_UPDATE, json.dumps(complete_update))

                
                if not significant_change and current_time - last_console_log > 20:
                    print(f"MQTT: {spaceCounter}/{len(poslist)} vagas livres (periódico)")
                    last_console_log = current_time
                last_update_time = current_time

            except Exception as e:
                print(f"Erro ao publicar no MQTT: {e}")

        previous_status = current_status.copy()

    
    cvzone.putTextRect(img, f'Livre:{spaceCounter}/{len(poslist)}', (100, 50),
                       scale=3, thickness=5, offset=20, colorR=(0, 200, 0))

print("Sistema de Detecção com MQTT iniciado!")
print("Aguardando conexão com o broker MQTT...")
print(f"Velocidade inicial: {VIDEO_SPEED}x | Pausa: {PAUSE_BETWEEN_FRAMES}ms")
print("Controles: [+/-] velocidade | [p] pausa | [q] sair")

while True:
    
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    success, img = cap.read()
    if not success:
        break

    
    imgGrey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGrey, (3, 3), 1)
    imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 25, 16)
    imgMedian = cv2.medianBlur(imgThreshold, 5)
    kernel = np.ones((3, 3), np.uint8)
    imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

    
    checkParkingSpace(imgDilate)

    
    cv2.imshow("Detector de Vagas - MQTT", img)

    
    key = cv2.waitKey(max(1, PAUSE_BETWEEN_FRAMES))
    if key == ord('q'):
        print("Encerrando sistema...")
        break
    elif key == ord('+'):
        
        if VIDEO_SPEED < 2.0:
            VIDEO_SPEED += 0.1
            print(f"Velocidade aumentada: {VIDEO_SPEED:.1f}x")
    elif key == ord('-'):
        
        if VIDEO_SPEED > 0.1:
            VIDEO_SPEED -= 0.1
            print(f"Velocidade diminuída: {VIDEO_SPEED:.1f}x")
    elif key == ord('p'):
        
        if PAUSE_BETWEEN_FRAMES == 0:
            PAUSE_BETWEEN_FRAMES = 100
            print("Vídeo PAUSADO (pressione 'p' novamente para continuar)")
        else:
            PAUSE_BETWEEN_FRAMES = 0
            print(f"Vídeo em movimento (velocidade: {VIDEO_SPEED:.1f}x)")
    elif key == ord('s'):
        
        VIDEO_SPEED = 0.5
        PAUSE_BETWEEN_FRAMES = 30
        print(f"Velocidade resetada: {VIDEO_SPEED:.1f}x | Pausa: {PAUSE_BETWEEN_FRAMES}ms")

cap.release()
cv2.destroyAllWindows()
if client:
    client.loop_stop()
    client.disconnect()