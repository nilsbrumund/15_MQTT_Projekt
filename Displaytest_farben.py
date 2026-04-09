from machine import Pin, SPI
import st7789py as st7789
import time
import vga2_16x32 as font

# ---Display Init-----------
spi = SPI(2, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(39), mosi=Pin(40))
custom_rotations = (
        (0x00, 170, 320, 35, 0, False),
        (0x60, 320, 170, 0, 35, False),
        (0xC0, 170, 320, 35, 0, False),
        (0xA0, 320, 170, 0, 35, False),
        )

tft = st7789.ST7789(
    spi, 170, 320,
    reset=Pin(37, Pin.OUT),
    cs=Pin(35, Pin.OUT),
    dc=Pin(36, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    custom_rotations=custom_rotations,
    rotation=1,
    color_order=st7789.BGR,
)
tft.inversion_mode(True)
tft.fill(st7789.BLACK)

# --------Variablen definieren--------------
header = "Nils-Empfaenger"
x1 = 0; y1 = 0; y2 = 32; y3 = 64; y4 = 96; y5 = 128
temp=27.91
humi=80


tft.text(font, header,  x1, y1, st7789.WHITE,  st7789.BLACK)
tft.text(font, f"Temp: {temp}C",   x1, y2, st7789.YELLOW, st7789.BLACK)
tft.text(font, f"Humi: {humi}%",   x1, y3, st7789.CYAN,   st7789.BLACK)
