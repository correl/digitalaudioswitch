import utime
from machine import Pin


class Button:
    DEBOUNCE_MS = 50
    DOUBLECLICK_MS = 400
    HOLD_MS = 1000

    def __init__(self, pin: Pin) -> None:
        self._pin = pin
        self._pressed = False
        self._clicked = False
        self._doubleclicked = False
        self._held = False

        self._debounce = 0
        self._hold = 0
        self._doubleclick = 0

        if self._pin():
            self._debounce = utime.ticks_ms()

    def update(self) -> None:
        now = utime.ticks_ms()

        if self._pin():
            if self._debounce and now - self._debounce >= self.DEBOUNCE_MS:
                self._debounce = 0
                self._pressed = True
                self._hold = now
            elif not self._pressed and not self._debounce:
                self._debounce = now
            elif self._hold and now - self._hold >= self.HOLD_MS:
                self._hold = 0
                self._held = True
        else:
            if self._pressed:
                self._pressed = False
                if self._doubleclick:
                    if now - self._doubleclick <= self.DOUBLECLICK_MS:
                        self._doubleclicked = True
                        self._doubleclick = 0
                        self._hold = 0
                        self._held = False
                else:
                    self._doubleclick = now
            if self._doubleclick and now - self._doubleclick > self.DOUBLECLICK_MS:
                if not self._held:
                    self._clicked = True
                self._doubleclick = 0
                self._hold = 0
                self._held = False

    def pressed(self) -> bool:
        return self._pressed

    def was_clicked(self) -> bool:
        if self._clicked:
            self._clicked = False
            return True
        return False

    def was_double_clicked(self) -> bool:
        if self._doubleclicked:
            self._doubleclicked = False
            return True
        return False

    def held(self) -> bool:
        return self._held


if __name__ == "__main__":
    button = Button(Pin(36, Pin.IN))
    while True:
        button.update()
        if button.was_clicked():
            print("CLICKED")
        if button.was_double_clicked():
            print("DOUBLE-CLICKED")
        if button.held():
            print("HELD")
        utime.sleep_ms(10)
