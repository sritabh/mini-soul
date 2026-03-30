# How to communicate with other minisouls

ESPNow allows for broadcasting messages.

> Broadcast when you touched and UART communication should allow to understand that it was touched, once touched we can broadcast and communicate information,

> this communication can also allow to share information and affection

# Deep sleep

Waking up with connecting pin to high(3.3v)

```python
from machine import Pin, deepsleep, reset_cause, wake_reason, DEEPSLEEP_RESET
from neopixel import NeoPixel
from time import sleep
import esp32
import machine

np = NeoPixel(Pin(48), 1)

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

cause = reset_cause()

if cause == DEEPSLEEP_RESET:
    reason = wake_reason()
    if reason == machine.EXT0_WAKE:      # 2
        set_color(0, 255, 0)    # GREEN = button
    elif reason == machine.TIMER_WAKE:   # 4
        set_color(255, 0, 0)  # RED = timer
    else:
        set_color(255, 255, 255) # WHITE = unexpected, tells us something is wrong
else:
    set_color(255, 0, 255)      # PURPLE = first boot

sleep(3)
set_color(0, 0, 0)
sleep(0.1)

# Setup wakeup
wake1 = Pin(2, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=wake1, level=esp32.WAKEUP_ANY_HIGH)

deepsleep(10000)
```

wake_on_ext0 and wake_on_ext1 sometime just don't show up as resource

Verify using

```python
import machine
import esp32

wake1 = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_DOWN)
print("Pin OK")

esp32.wake_on_ext0(pin=wake1, level=esp32.WAKEUP_ANY_HIGH)
print("wake_on_ext0 OK")
```

And

```python
import machine
import esp32

wake1 = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_DOWN)
print("Pin OK")

esp32.wake_on_ext1(pins=(wake1,), level=esp32.WAKEUP_ANY_HIGH)
print("wake_on_ext1 OK")
```

This probably is because of once the resource is used, it gets locked and doesn't get released. When we restart the device, it starts working.


# Making touch work

this works weirdly, it seems like the connected wire is acting as antenna getting em interference and triggering the touch causing it to wake automatically. But when pin like 12 which is not connected to anything is used, the touch works as expected. On search claude suggested to use 1m ohm resistor to make the em interference less likely to trigger the touch.

```python
from machine import Pin, deepsleep, reset_cause, wake_reason, DEEPSLEEP_RESET
from neopixel import NeoPixel
from time import sleep
import esp32
import machine

np = NeoPixel(Pin(48), 1)

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

cause = reset_cause()

if cause == DEEPSLEEP_RESET:
    reason = wake_reason()
    if reason == machine.TIMER_WAKE:
        set_color(255, 0, 0)    # RED = timer, nothing touched
    elif reason == machine.EXT0_WAKE:
        set_color(0, 255, 255)  # CYAN = touch triggered it
    else:
        set_color(255, 255, 255) # WHITE = unexpected
else:
    set_color(128, 0, 255)      # PURPLE = first boot

sleep(3)
set_color(0, 0, 0)
sleep(0.1)

wake_pin = Pin(10, Pin.IN, Pin.PULL_DOWN)
esp32.wake_on_ext0(pin=wake_pin, level=esp32.WAKEUP_ANY_HIGH)

deepsleep(7000)

```


# Using lightsleep instead

We can go to sleep every 100ms and check if the touch is active to trigger wake else go back to sleep again
```python
from machine import Pin, TouchPad, lightsleep
from neopixel import NeoPixel
from time import sleep

np = NeoPixel(Pin(48), 1)

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

t = TouchPad(Pin(4))
sleep(1)
baseline = t.read()
touch_threshold = int(baseline * 1.2)

print(f"baseline={baseline} touch_threshold={touch_threshold}")

def is_touched():
    return t.read() > touch_threshold

set_color(255, 0, 0)        # RED = awake
sleep(1)

          # OFF = light sleeping
while True:
    set_color(0, 0, 0)
    lightsleep(100)            # sleep 5s then poll

    if is_touched():
        set_color(0, 255, 0)    # GREEN = touch detected
        sleep(2)

```

> Deepsleep takes longer time to wake as whole micropython restarts. Probably not a good idea
