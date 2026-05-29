import cv2
from ultralytics import YOLO

model = YOLO('/home/ras/EMBEBIDOS2/model/best_clasification_50.onnx', task='classify') 

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("No se pudo acceder a la camara.")
    exit()

nombres_clases = model.names
print(f"Clases cargadas en la Pi: {nombres_clases}")
print("Clasificador embebido corriendo. Presiona 'q' para salir.")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    results = model(frame, imgsz=224, device='cpu', verbose=False)
    
    probs = results[0].probs
    idx_ganador = probs.top1 
    nombre_ganador = results[0].names[idx_ganador]
    confianza_ganadora = probs.top1conf.item()

    idx_fondo = None
    for idx, name in results[0].names.items():
        if name.lower() == 'fondo':
            idx_fondo = idx
            break
            
    porcentaje_fondo = probs.data[idx_fondo].item() if idx_fondo is not None else 0.0

    if porcentaje_fondo > 0.75:
        clase_vista = "fondo"
        confianza = porcentaje_fondo
        color = (0, 0, 255) 
    else:
        clase_vista = nombre_ganador
        confianza = confianza_ganadora
        color = (0, 255, 0) 

    texto_pantalla = f"Viendo: {clase_vista.upper()} ({confianza * 100:.1f}%)"
    cv2.putText(frame, texto_pantalla, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)

    print(f"Pi detectando: {clase_vista.upper()} | Fondo: {porcentaje_fondo*100:.1f}%", end="\r")

    cv2.imshow("Raspberry Pi 4 - Clasificador", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Sistema cerrado.")