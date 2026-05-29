import cv2
import serial
import time
from ultralytics import YOLO
import matplotlib.pyplot as plt

try:
    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=0.05)
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
duracion_total = 60.0  
tiempo_acumulado = 0.0
inicio_tiempo = time.time()

sistema_activo = True  
ya_conto_esta_botella = False  

ultimo_comando_enviado = "N"
clase_candidata = "fondo"
conteo_estabilidad = 0
UMBRAL_CUADROS_CONSECUTIVOS = 6 

while cap.isOpened():
    if ser.in_waiting > 0:
        char_recibido = ser.read().decode('utf-8', errors='ignore')
        if char_recibido == 'E':
            sistema_activo = not sistema_activo  
            if sistema_activo:
                inicio_tiempo = time.time() - tiempo_acumulado
                print("Sistema Reanudado")
            else:
                tiempo_acumulado = time.time() - inicio_tiempo
                print("Sistema Pausado")

    success, frame = cap.read()
    if not success: break

    if not sistema_activo:
        cv2.rectangle(frame, (0, 0), (640, 480), (0, 0, 150), 6) 
        cv2.putText(frame, "PARADA DE EMERGENCIA ACTIVA", (40, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.putText(frame, "Conteo guardado en memoria", (60, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.imshow("Raspberry Pi 4 - Transmisor UART Filtrado", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        continue

    tiempo_actual_valido = time.time() - inicio_tiempo
    tiempo_restante = max(0.0, duracion_total - tiempo_actual_valido)

    if tiempo_restante <= 0:
        print("Tiempo cumplido")
        break

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
        
        if clase_estable == 'coca': comando_uart = 'C'
        elif clase_estable == 'fanta': comando_uart = 'F'
        elif clase_estable == 'pepsi': comando_uart = 'P'
        elif clase_estable == 'salvietti': comando_uart = 'S'
        else: comando_uart = 'N'

        if clase_estable != 'fondo':
            if not ya_conto_esta_botella:
                diccionario_conteo[clase_estable] += 1
                ya_conto_esta_botella = True  
                print(f"Registrado: {clase_estable.upper()} | Total: {diccionario_conteo[clase_estable]}")
        else:
            ya_conto_esta_botella = False 

        if comando_uart != ultimo_comando_enviado:
            try:
                ser.write(comando_uart.encode('utf-8'))
                ultimo_comando_enviado = comando_uart
            except Exception as e:
                print(f"Fallo UART: {e}")

    color = (0, 0, 255) if ultimo_comando_enviado == 'N' else (0, 255, 0)
    cv2.putText(frame, f"Viendo: {clase_candidata.upper()}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(frame, f"Tiempo: {int(tiempo_restante)}s", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    y_offset = 360
    for key, val in diccionario_conteo.items():
        cv2.putText(frame, f"{key.upper()}: {val}", (30, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_offset += 25

    cv2.imshow("Raspberry Pi 4 - Transmisor UART Filtrado", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
ser.close()
cv2.destroyAllWindows()

with open("conteo_botellas.txt", "w") as f:
    f.write("=======================================\n")
    f.write("      REPORTE FINAL DE PRODUCCION      \n")
    f.write(f"Fecha/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=======================================\n")
    for botella, total in diccionario_conteo.items():
        f.write(f"- {botella.upper()}: {total} unidades.\n")
    f.write("=======================================\n")
print("Archivo generado")

top_3 = sorted(diccionario_conteo.items(), key=lambda item: item[1], reverse=True)[:3]
nombres_top3 = [item[0].upper() for item in top_3]
valores_top3 = [item[1] for item in top_3]

plt.figure(figsize=(8, 5))
colores_barras = ['#ff0000', '#ff8800', '#0000ff'] 
plt.bar(nombres_top3, valores_top3, color=colores_barras, edgecolor='black', width=0.6)

plt.title("Top 3 Refrescos Mas Detectados", fontsize=14, fontweight='bold')
plt.xlabel("Tipo de Botella", fontsize=12)
plt.ylabel("Cantidad de Unidades", fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.yticks(range(0, max(valores_top3) + 3 if valores_top3 else 5))

plt.savefig("grafico_produccion.png")
print("Grafico guardado")
plt.show()
