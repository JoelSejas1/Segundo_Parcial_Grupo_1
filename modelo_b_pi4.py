import cv2
import serial
import time
from ultralytics import YOLO
import matplotlib.pyplot as plt

try:

    ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
    print("Puerto UART abierto correctamente (Modo Receptor)")
except Exception as e:
    print(f"Error UART: {e}")
    exit()

model = YOLO('/home/ras/EMBEBIDOS2/model/best_clasification_50.onnx', task='classify') 

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Error: no camara")
    exit()

nombres_clases = model.names
print("Clasificador con Filtro corriendo por 60 segundos...")

clase_candidata = "fondo"
conteo_estabilidad = 0
UMBRAL_CUADROS_CONSECUTIVOS = 6  

conteo_botellas = {'coca': 0, 'fanta': 0, 'pepsi': 0, 'salvietti': 0}
ultima_estable = "fondo"
tiempo_inicio = time.time()
duracion = 60 

while cap.isOpened():
    if time.time() - tiempo_inicio >= duracion:
        print("Tiempo cumplido (1 minuto) -> Saliendo del bucle")
        break

    success, frame = cap.read()
    if not success: break

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
        
    
        if clase_estable != ultima_estable:
            if clase_estable in conteo_botellas:
                conteo_botellas[clase_estable] += 1
                print(f"-> NUEVO CONTEO: {clase_estable} = {conteo_botellas[clase_estable]}")
            ultima_estable = clase_estable


    tiempo_restante = int(duracion - (time.time() - tiempo_inicio))
    
 
    cv2.putText(frame, f"Estable: {clase_candidata.upper()}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Tiempo: {tiempo_restante}s", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Raspberry Pi 4 - Receptor UART y Filtro", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()


print("\PROCESANDO RESULTADOS")
top_3 = sorted(conteo_botellas.items(), key=lambda x: x[1], reverse=True)[:3]
print("Top 3:", top_3)

f = open("resultado_conteo.txt", "w")
f.write("=== RESULTADOS DEL CONTEO (1 MINUTO) ===\n")
f.write(f"1er Lugar: {top_3[0][0].upper()} - Cantidad: {top_3[0][1]}\n")
f.write(f"2do Lugar: {top_3[1][0].upper()} - Cantidad: {top_3[1][1]}\n")
f.write(f"3er Lugar: {top_3[2][0].upper()} - Cantidad: {top_3[2][1]}\n")
f.write("\nConteo Completo:\n")
for k, v in conteo_botellas.items():
    f.write(f"- {k}: {v}\n")
f.close()
print("Archivo TXT guardado.")

marcas = [top_3[0][0], top_3[1][0], top_3[2][0]]
valores = [top_3[0][1], top_3[1][1], top_3[2][1]]

plt.bar(marcas, valores, color='blue')
plt.title('Top 3 Botellas Mas Detectadas')
plt.xlabel('Botella')
plt.ylabel('Cantidad')
plt.show()