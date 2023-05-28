"""MicroPython CD4052B Analog Multiplexer driver

Driver for the 8-channel analog multiplexer with logic-level conversion from
Texas Instruments. (https://www.ti.com/lit/ds/symlink/cd4051b.pdf)

The CD4052B switches up to four pairs of inputs or outputs, numbered 0 through
3, mapping them to the two common pins.

Copyright 2023 Correl Roush

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the “Software”), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""


from machine import Pin


class CD4052:
    def __init__(self, channel_select_a: int, channel_select_b: int, inh: int):
        self._channel_select_a = Pin(channel_select_a, Pin.OUT)
        self._channel_select_b = Pin(channel_select_b, Pin.OUT)
        self._inh = Pin(inh, Pin.OUT)

    def select(self, channel: int) -> None:
        """Select a channel pair between 0 and 3.

        The device will be muted during the switch. Mute will be re-enabled once
        the switch is complete if the device wasn't already muted.

        """
        a = channel & 0b01
        b = (channel & 0b10) >> 1
        print(f"CD4052: Selecting Channel {channel} ({a}, {b})")
        mute = self._inh()
        self._inh.on()
        self._channel_select_a(a)
        self._channel_select_b(b)
        self._inh(mute)

    def channel(self) -> int:
        """Retrieve the currently selected channel pair."""
        return self._channel_select_a() | (self._channel_select_b() << 1)

    def muted(self) -> bool:
        """Return the mute status."""
        return bool(self._inh())

    def mute(self, value: bool = True) -> None:
        """Mute the device."""
        self._inh(value)

    def unmute(self) -> None:
        """Unmute the device."""
        self._inh(False)

    def toggle_mute(self) -> None:
        """Togggle mute."""
        self._inh(not self._inh())


if __name__ == "__main__":
    switch = CD4052(18, 19, 23)
    switch.select(0)
