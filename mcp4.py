"""MicroPython MCP413X/415X/423X/425X SPI driver

Driver for the 7/8-Bit Single/Dual SPI Digital POT with Volatile Memory from
Microchip. (https://ww1.microchip.com/downloads/en/DeviceDoc/22060b.pdf)

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

from machine import Pin, SPI


class NetworkControl:
    def __init__(self, hw=True, a=True, w=True, b=True) -> None:
        self.forced_hardware_shutdown = hw
        self.terminal_a_connected = a
        self.wiper_connected = w
        self.terminal_b_connected = b

    @staticmethod
    def from_bin(data: int) -> "NetworkControl":
        return NetworkControl(
            hw=bool(data & 0b1000),
            a=bool(data & 0b0100),
            w=bool(data & 0b0010),
            b=bool(data & 0b0001),
        )

    def __repr__(self):
        return "<Network HW={hw} A={a} W={w} B={b}".format(
            hw=self.forced_hardware_shutdown,
            a=self.terminal_a_connected,
            w=self.wiper_connected,
            b=self.terminal_b_connected,
        )


class TerminalControl:
    def __init__(self, resistor_0: NetworkControl, resistor_1: NetworkControl) -> None:
        self.resistor_0 = resistor_0
        self.resistor_1 = resistor_1

    @staticmethod
    def from_bin(data: int) -> "TerminalControl":
        return TerminalControl(
            resistor_0=NetworkControl.from_bin(data),
            resistor_1=NetworkControl.from_bin(data >> 4),
        )

    def __repr__(self):
        return "<Terminals 0:{r0} 1:{r1}>".format(
            r0=self.resistor_0,
            r1=self.resistor_1,
        )


class MCP4:
    """MicroPython MCP413X/415X/423X/425X SPI driver"""

    ADDRESS_WIPER_0 = 0x00
    ADDRESS_WIPER_1 = 0x01
    ADDRESS_TCON = 0x04
    ADDRESS_STATUS = 0x05

    CMD_WRITE = 0b00
    CMD_INCREMENT = 0b01
    CMD_DECREMENT = 0b10
    CMD_READ = 0b11

    def __init__(self, spi: SPI, cs: Pin) -> None:
        self.spi = spi
        self.cs = cs

    def _bytes(self, address: int, command: int, data: int = 0x0) -> bytearray:
        """Translate an address, command, and data into bytes to send.

        - Address is a 4-bit memory address.
        - Command is a 2-bit command code.
        - Data is 2 bits for increment and decrement operations (ignored), and
          10 bits for read and write operations.

        """
        command_byte = address << 4 & 0b11110000 | command << 2 & 0b00001100
        if command in (0b00, 0b11):
            # Include data byte for 10 total bits of data
            return bytearray([command_byte | (0b11 & data >> 8), data & 0xFF])
        return bytearray([command_byte])

    def _write(self, data: bytearray) -> bytearray:
        """Write data to the SPI interface, returning its output."""
        output = bytearray(len(data))
        self.spi.write_readinto(data, output)
        return output

    def do(self, address: int, command: int, data: int = 0x0) -> int:
        """Execute a command on the MCP4, returning its integer result."""
        self.cs(0)
        output = self._write(self._bytes(address, command, data))
        self.cs(1)

        OK = 0b11111110
        if OK != output[0] & OK:
            self.cs(0)
            raise ValueError("Invalid command")
        result = output[0] & 0b01
        if len(output) > 1:
            result <<= 8
            result |= output[1]
        return result

    def increment(self, wiper: int = 0) -> int:
        """Increment a wiper."""
        return self.do(
            address=self.ADDRESS_WIPER_1 if wiper == 1 else self.ADDRESS_WIPER_0,
            command=self.CMD_INCREMENT,
        )

    def decrement(self, wiper: int = 0) -> int:
        """Decrement a wiper."""
        return self.do(
            address=self.ADDRESS_WIPER_1 if wiper == 1 else self.ADDRESS_WIPER_0,
            command=self.CMD_DECREMENT,
        )

    def read(self, wiper: int = 0) -> int:
        """Read the current value of a wiper."""
        return self.do(
            address=self.ADDRESS_WIPER_1 if wiper == 1 else self.ADDRESS_WIPER_0,
            command=self.CMD_READ,
        )

    def write(self, wiper: int = 0, data: int = 0x00) -> int:
        """Set a value for a wiper."""
        return self.do(
            address=self.ADDRESS_WIPER_1 if wiper == 1 else self.ADDRESS_WIPER_0,
            command=self.CMD_WRITE,
            data=data,
        )

    def is_shutdown(self) -> bool:
        status = self.do(address=self.ADDRESS_STATUS, command=self.CMD_READ)
        return status & 0b10 == 0b10

    @property
    def control(self) -> TerminalControl:
        data = self.do(address=self.ADDRESS_TCON, command=self.CMD_READ)
        return TerminalControl.from_bin(data)
