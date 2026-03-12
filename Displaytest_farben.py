from machine import Pin, SPI
import st7789py as st7789
import time

# ── Init ───────────────────────────────────────────────────
bl = Pin(15, Pin.OUT)
bl.value(1)

spi = SPI(2, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(8))
custom_rotations = (
        (0x00, 170, 320, 35, 0, False),
        (0x60, 320, 170, 0, 35, False),
        (0xC0, 170, 320, 35, 0, False),
        (0xA0, 320, 170, 0, 35, False),
    )

tft = st7789.ST7789(
    spi, 170, 320,
    reset=Pin(4,  Pin.OUT),
    cs=Pin(5,     Pin.OUT),
    dc=Pin(2,     Pin.OUT),
    backlight=Pin(15, Pin.OUT),
    custom_rotations=custom_rotations,
    rotation=0,
    color_order=st7789.BGR,
)
tft.inversion_mode(True)

# ── Test 1: Vollbild-Farben ────────────────────────────────
for farbe, name in [
    (st7789.RED,    "Rot"),
    (st7789.GREEN,  "Grün"),
    (st7789.BLUE,   "Blau"),
    (st7789.YELLOW, "Gelb"),
    (st7789.WHITE,  "Weiß"),
    (st7789.BLACK,  "Schwarz"),
]:
    print(f"Farbe: {name}")
    tft.fill(farbe)
    time.sleep(0.8)

# ── Test 2: Rechtecke ─────────────────────────────────────
tft.fill(st7789.BLACK)
tft.fill_rect(10,  10, 100, 100, st7789.RED)
tft.fill_rect(120, 10, 100, 100, st7789.GREEN)
tft.fill_rect(10, 120, 100, 100, st7789.BLUE)
tft.fill_rect(120,120, 100, 100, st7789.YELLOW)
time.sleep(2)

# ── Test 3: Linien ────────────────────────────────────────
tft.fill(st7789.BLACK)
tft.hline(0, 160, 240, st7789.WHITE)   # Horizontal
tft.vline(120, 0, 320, st7789.WHITE)   # Vertikal
time.sleep(2)

# ── Test 4: Pixel-Diagonale ───────────────────────────────
tft.fill(st7789.BLACK)
for i in range(240):
    tft.pixel(i, int(i * 320/240), st7789.CYAN)

print("Alle Tests abgeschlossen!")