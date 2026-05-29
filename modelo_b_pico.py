from machine import Pin, UART
import time

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1), timeout=10)
boton_emergencia = Pin(16, Pin.IN, Pin.PULL_UP)

ultimo_tiempo_pulsado = 0
INTERVALO_DEBOUNCE_MS = 300 

def manejar_emergencia(pin):
    global ultimo_tiempo_pulsado
    tiempo_actual = time.ticks_ms()
    if time.ticks_diff(tiempo_actual, ultimo_tiempo_pulsado) > INTERVALO_DEBOUNCE_MS:
        ultimo_tiempo_pulsado = tiempo_actual
        uart.write(b'E')
        print("Emergencia 'E' enviada")

boton_emergencia.irq(trigger=Pin.IRQ_FALLING, handler=manejar_emergencia)

while True:
    time.sleep(1)
