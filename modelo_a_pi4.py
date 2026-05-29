import cv2
import serial
import time
from ultralytics import YOLO
try:
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
    print("Puerto UART abierto correctamente")
except Exception as e:
    print(f"Error al abrir el puerto UART: {e}")
    exit()
model = YOLO('/home/ras/EMBEBIDOS2/model/best_clasification_50.onnx', task='classify') 

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Error: no camara")
    exit()

nombres_clases = model.names
print("Clasificador con Filtro, presiona 'q' para salir.")

ultimo_comando_enviado = "N"
clase_candidata = "fondo"
conteo_estabilidad = 0
UMBRAL_CUADROS_CONSECUTIVOS = 6  

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    results = model(frame, imgsz=224, device='cpu', verbose=False)
    
    probs = results[0].probs
    idx_ganador = probs.top1 
    nombre_ganador = results[0].names[idx_ganador]
    confianza_ganador = probs.top1conf.item()

    idx_fondo = None
    for idx, name in results[0].names.items():
        if name.lower() == 'fondo':
            idx_fondo = idx
            break
            
    porcentaje_fondo = probs.data[idx_fondo].item() if idx_fondo is not None else 0.0

    if porcentaje_fondo > 0.80:  
        clase_actual = "fondo"
        confianza = porcentaje_fondo
    else:
        clase_actual = nombre_ganador
        confianza = confianza_ganador

    if clase_actual == clase_candidata:
        conteo_estabilidad += 1
    else:
        clase_candidata = clase_actual
        conteo_estabilidad = 1

    if conteo_estabilidad >= UMBRAL_CUADROS_CONSECUTIVOS:
        clase_estable = clase_candidata
        
        if clase_estable == 'coca': comando_uart = 'C'
        elif clase_estable == 'fanta': comando_uart = 'F'
        elif clase_estable == 'pepsi': comando_uart = 'P'
        elif clase_estable == 'salvietti': comando_uart = 'S'
        else: comando_uart = 'N'

        if comando_uart != ultimo_comando_enviado:
            try:
                ser.write(comando_uart.encode('utf-8'))
                ultimo_comando_enviado = comando_uart
                print(f"UART ENVIADO -> [{comando_uart}] Confirmado: {clase_estable.upper()}")
            except Exception as e:
                print(f"Fallo UART: {e}")

    color = (0, 0, 255) if ultimo_comando_enviado == 'N' else (0, 255, 0)
    texto_pantalla = f"Estable: {clase_candidata.upper()} ({confianza * 100:.1f}%)"
    cv2.putText(frame, texto_pantalla, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)

    cv2.imshow("Raspberry Pi 4 - transmisor UART Filtrado", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()
