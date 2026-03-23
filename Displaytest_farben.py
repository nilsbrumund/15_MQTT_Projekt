from machine import Pin, SPI
import st7789py as st7789
import time
import vga2_16x32 as font

# ── Init ───────────────────────────────────────────────────
bl = Pin(35, Pin.OUT)
bl.value(1)

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
    reset=Pin(37,  Pin.OUT),
    cs=Pin(35,     Pin.OUT),
    dc=Pin(36,     Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    custom_rotations=custom_rotations,
    rotation=1,
    color_order=st7789.BGR,
)
tft.inversion_mode(True)

# ── Test 1: Vollbild-Farben
text1 = "Nils-Empfaenger"
text2 = "Babysteps"

char_h = 32

tft.fill(st7789.BLACK)

# ── Zeile 1: normal oben ───────────────────────────────────
tft.rotation(1)
x1 = (320 - len(text1) * 16) // 2
tft.text(font, text1, x1, 0, st7789.WHITE, st7789.BLACK)

# ── Zeile 2: 180° gedreht unten ───────────────────────────
tft.rotation(3)
# Bei 180° ist y=0 unten – also text2 erscheint unterhalb von text1
x2 = (320 - len(text2) * 16) // 2
tft.text(font, text2, x2, 0, st7789.YELLOW, st7789.BLACK)