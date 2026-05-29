from machine import Pin, UART, Timer
import time

led_rojo = Pin(8, Pin.OUT)
led_verde = Pin(9, Pin.OUT)

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1), timeout=10)

estado_actual = "N" 

timer_leds = Timer()

def controlar_leds(t):
    global estado_actual
    
    if estado_actual == "C":
        led_verde.off()
        led_rojo.toggle()
    elif estado_actual == "S":
        led_rojo.off()
        led_verde.toggle()
    else:
        led_rojo.toggle()
        led_verde.toggle()

timer_leds.init(period=1000, mode=Timer.PERIODIC, callback=controlar_leds)

print("Pico W lista y escuchando a la Pi 4...")

while True:
    if uart.any():
        datos = uart.readline().decode('utf-8').strip()
        if datos:
            print(f"Comando recibido: {datos}")
            estado_anterior = estado_actual
            estado_actual = datos
            
            if estado_actual in ["C", "S"]:
                if estado_anterior not in ["C", "S"]:
                    timer_leds.init(period=1000, mode=Timer.PERIODIC, callback=controlar_leds)
            else:
                if estado_anterior in ["C", "S"] or estado_anterior == "N":
                    timer_leds.init(period=3000, mode=Timer.PERIODIC, callback=controlar_leds)
            
            if estado_actual == "C":
                led_verde.off()
            elif estado_actual == "S":
                led_rojo.off()
                
    time.sleep(0.1)