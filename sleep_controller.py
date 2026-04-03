import machine
from machine import lightsleep, wake_reason


class WakeEvent:
    """Reason the device woke from lightsleep — a hardware fact."""
    TOUCH  = "touch"
    BUTTON = "button"


class SleepController:
    """Minimal sleep/wake utility.

    Owns only the lightsleep polling loop and touchpad state.
    All awake-phase logic (mode dispatch, button signals) lives in main.py.

    Usage:
        ctrl = SleepController(touch_pad, threshold, poll_ms=400)
        wake = ctrl.wait_for_wake()   # blocks; returns WakeEvent
    """

    def __init__(self, touch_pad, touch_threshold, poll_ms=400):
        self._touch_pad       = touch_pad
        self._touch_threshold = touch_threshold
        self._poll_ms         = poll_ms

    def is_touched(self):
        return self._touch_pad.read() > self._touch_threshold

    def wait_for_wake(self):
        """Block via lightsleep until button or touch wakes the device.
        Returns WakeEvent.BUTTON or WakeEvent.TOUCH."""
        while True:
            lightsleep(self._poll_ms)
            reason = wake_reason()
            if reason == machine.EXT0_WAKE:
                return WakeEvent.BUTTON
            if self.is_touched():
                return WakeEvent.TOUCH
