from machine import Pin, SPI, SoftI2C
import framebuf
import ssd1306
import mcp4


i2c = SoftI2C(sda=Pin(2), scl=Pin(16))
oled_width = 128
oled_height = 32
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
buf = bytearray((oled_height // 8) * oled_width)
fbuf = framebuf.FrameBuffer1(buf, oled_width, oled_height)


spi = SPI(1)
cs = Pin(15, mode=Pin.OUT, value=1)
pot = mcp4.MCP4(spi, cs)


def update():
    PW0 = pot.read(0)
    PW1 = pot.read(1)
    oled.fill(0)
    oled.text(f"PW0: {PW0}", 0, 0)
    oled.text(f"PW1: {PW1}", 0, 10)
    oled.show()


update()
