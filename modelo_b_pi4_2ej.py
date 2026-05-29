import cv2
import serial
import time
from ultralytics import YOLO

try:
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=0.01)
    print("UART OK")
except Exception as e:
    print(f"Error UART: {e}")
    exit()

model = YOLO('/home/ras/EMBEBIDOS2/model/best_clasification_50.onnx', task='classify') 

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Error Camara")
    exit()

diccionario_conteo = {'coca': 0, 'fanta': 0, 'pepsi': 0, 'salvietti': 0}
sistema_activo = True  
ya_conto_esta_botella = False  

clase_candidata = "fondo"
conteo_estabilidad = 0
UMBRAL_CUADROS_CONSECUTIVOS = 6 

while cap.isOpened():
    if ser.in_waiting > 0:
        char_recibido = ser.read().decode('utf-8', errors='ignore')
        if char_recibido == 'E':
            sistema_activo = not sistema_activo  
            if sistema_activo:
                print("Sistema Reanudado - Detectando")
            else:
                print("Sistema Pausado por Emergencia - Guardando TXT")
                with open("emergencia_conteo.txt", "w") as f:
                    f.write("=======================================\n")
                    f.write("    CONTEO GUARDADO POR EMERGENCIA     \n")
                    f.write(f"Hora de parada: {time.strftime('%H:%M:%S')}\n")
                    f.write("=======================================\n")
                    for botella, total in diccionario_conteo.items():
                        f.write(f"{botella.upper()}: {total}\n")
                    f.write("=======================================\n")

    success, frame = cap.read()
    if not success: break

    if not sistema_activo:
        cv2.rectangle(frame, (0, 0), (640, 480), (0, 0, 150), 6) 
        cv2.putText(frame, "PARADA DE EMERGENCIA ACTIVA", (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.putText(frame, "Conteo respaldado en emergencia_conteo.txt", (40, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_offset = 320
        for key, val in diccionario_conteo.items():
            cv2.putText(frame, f"CONGELADO -> {key.upper()}: {val}", (40, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            y_offset += 25
            
        cv2.imshow("Sistema - Control de Emergencia", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        continue

    results = model(frame, imgsz=224, device='cpu', verbose=False)
    probs = results[0].probs
    idx_ganador = probs.top1 
    nombre_ganador = results[0].names[idx_ganador]

    idx_fondo = None
    for idx, name in results[0].names.items():
        if name.lower() == 'fondo':
            idx_fondo = idx
            break
            
    porcentaje_fondo = probs.data[idx_fondo].item() if idx_fondo is not None else 0.0

    if porcentaje_fondo > 0.80: 
        clase_actual = "fondo"
    else:
        clase_actual = nombre_ganador

    if clase_actual == clase_candidata:
        conteo_estabilidad += 1
    else:
        clase_candidata = clase_actual
        conteo_estabilidad = 1

    if conteo_estabilidad >= UMBRAL_CUADROS_CONSECUTIVOS:
        clase_estable = clase_candidata

        if clase_estable != 'fondo':
            if not ya_conto_esta_botella:
                diccionario_conteo[clase_estable] += 1
                ya_conto_esta_botella = True  
                print(f"Registrado: {clase_estable.upper()} | Total: {diccionario_conteo[clase_estable]}")
        else:
            ya_conto_esta_botella = False 

    color = (0, 255, 0)
    cv2.putText(frame, f"ESTADO: OPERANDO CORRECTAMENTE", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Viendo actual: {clase_candidata.upper()}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    
    y_offset = 340
    for key, val in diccionario_conteo.items():
        cv2.putText(frame, f"{key.upper()}: {val}", (30, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        y_offset += 25

    cv2.imshow("Sistema - Control de Emergencia", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
ser.close()
cv2.destroyAllWindows()