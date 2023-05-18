import unittest

import mcp4


class CommandTests(unittest.TestCase):
    def assertBitsEqual(self, data: bytearray, expected: str):
        self.assertEqual(
            "".join("{:08b}".format(byte) for byte in data),
            expected.replace(" ", ""),
        )

    def test_increment(self) -> None:
        self.assertBitsEqual(mcp4.command_bytes(0b0000, 0b01, 0b00), "0000 01 00")
        self.assertBitsEqual(mcp4.command_bytes(0b0001, 0b01, 0b00), "0001 01 00")

    def test_decrement(self) -> None:
        self.assertBitsEqual(mcp4.command_bytes(0b0000, 0b10, 0b00), "0000 10 00")
        self.assertBitsEqual(mcp4.command_bytes(0b0001, 0b10, 0b00), "0001 10 00")

    def test_read(self) -> None:
        self.assertBitsEqual(
            mcp4.command_bytes(0b0000, 0b11, 0b0000000000),
            "0000 11 00 0000 0000",
        )

    def test_write(self) -> None:
        self.assertBitsEqual(
            mcp4.command_bytes(0b0000, 0b00, 0b0001111111),
            "0000 00 00 0111 1111",
        )
