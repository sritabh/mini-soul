"""
sim/machine.py — Stub for the MicroPython `machine` module.

Only the subset used by the project is implemented; everything is a no-op
unless noted.
"""


class Pin:
    OUT      = 1
    IN       = 0
    PULL_DOWN = 0
    PULL_UP   = 1
    IRQ_RISING  = 1
    IRQ_FALLING = 2

    def __init__(self, n, mode=IN, pull=None, value=None):
        self._val = value if value is not None else 0

    def value(self, v=None):
        if v is not None:
            self._val = v
        return self._val

    def irq(self, trigger=None, handler=None):
        pass


class Timer:
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, id=-1):
        pass

    def init(self, period=0, mode=ONE_SHOT, callback=None):
        pass

    def deinit(self):
        pass


class SoftI2C:
    def __init__(self, sda=None, scl=None, freq=400_000):
        pass
