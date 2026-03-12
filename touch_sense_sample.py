from machine import TouchPad, Pin
import time

touch = TouchPad(Pin(7))

while True:
    val = touch.read()
    print("Touch value:", val)
    time.sleep_ms(200)
