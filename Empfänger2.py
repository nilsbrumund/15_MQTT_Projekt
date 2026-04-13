import network, time, json
from machine import Pin, SPI
from umqtt.simple import MQTTClient
import st7789py as st7789
import vga2_16x32 as font
# --- WLAN ---
"""
WLAN_SSID = "BZTG_local"
WLAN_PASS = "Mittelsenkrechte64"
"""
WLAN_SSID = "FRITZ!Box NB"
WLAN_PASS = "46914294587536504239"
# --- MQTT ---
MQTT_SERVER  = "192.168.178.23"
CLIENT_ID    = "Nils_ESP2"
BROKER_USER  = "NilsMQTT"
BROKER_PW    = "passwort"
TOPIC_WERTE  = "projekt/werte"
TOPIC_STATUS = "projekt/status"
# --- Globalvariablen ---
data = {"temp": 0, "humi": 0, "ligh": 0}
status = "OFFLINE"
last_update = time.ticks_ms()
last_ping = time.ticks_ms()
start_time = time.ticks_ms()
last_msg_time = time.ticks_ms()

def wlan_verbinden(timeout=30):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(0.5)
    wlan.active(True)
    wlan.connect(WLAN_SSID, WLAN_PASS)
    for _ in range(timeout):
        if wlan.isconnected():
            print("Verbunden:", wlan.ifconfig()[0])
            return wlan
        print("Warten...")
        time.sleep(1)
    raise RuntimeError("Verbindungsaufbau WLAN fehlgeschlagen")

wlan_verbinden()

# --- Display ---
spi = SPI(2, baudrate=20000000, polarity=0, phase=0, sck=Pin(39), mosi=Pin(40))
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

# --- Displayausgabe ---
x1 = 0
y1, y2, y3, y4, y5 = 0, 32, 64, 96, 128

def display_update(status, temp, humi, ligh, uptime, since_last):
    tft.text(font, f"Status: {status}   ", x1, y1, st7789.WHITE,  st7789.BLACK)
    tft.text(font, f"Temp: {temp}C    ", x1, y2, st7789.YELLOW, st7789.BLACK)
    tft.text(font, f"Humi: {humi}%    ", x1, y3, st7789.CYAN,   st7789.BLACK)
    tft.text(font, f"Ligh: {ligh}lux  ", x1, y4, st7789.YELLOW, st7789.BLACK)
    tft.text(font, f"Time: {uptime}s Last: {since_last}s  ", x1, y5, st7789.WHITE,  st7789.BLACK)

def on_message(topic, msg):
    global data, status, last_msg_time
    topic = topic.decode()
    msg   = msg.decode()
    last_msg_time = time.ticks_ms()
    
    if topic == TOPIC_WERTE:
        try:
            data = json.loads(msg)
            print("Empfangen:", data)
        except ValueError:
            print("Ungültiges JSON erhalten:", msg)

    elif topic == TOPIC_STATUS:
        if msg == "online":
            status = "ONLINE"
        elif msg == "offline":
            status = "OFFLINE (LWT)"
        else:
            status = "UNKNOWN"
        print("Status:", status)

def mqtt_connect():
    client = MQTTClient(CLIENT_ID, MQTT_SERVER, port=1883, user=BROKER_USER, password=BROKER_PW, keepalive=15)
    client.set_callback(on_message)
    client.connect(clean_session=True)
    client.subscribe(TOPIC_WERTE)
    client.subscribe(TOPIC_STATUS)
    print("MQTT verbunden")
    return client

client = mqtt_connect()
display_update(status, 0, 0, 0, 0, 0)

#--- Loop ---
while True:
    try:
        client.check_msg()

        now = time.ticks_ms()
        
        #Ping für KA
        if time.ticks_diff(now, last_ping) >= 10000:
            client.ping()
            last_ping = now
            print("Ping gesendet")
        #Display
        if time.ticks_diff(now, last_update) >= 1000:
            uptime = time.ticks_diff(now, start_time) // 1000
            since_last = time.ticks_diff(now, last_msg_time) // 1000
            display_update(status, data["temp"], data["humi"], data["ligh"], uptime, since_last)
            last_update = now

    except OSError as e:
        import sys
        sys.print_exception(e)
        status = "OFFLINE"
        uptime = time.ticks_diff(time.ticks_ms(), start_time) // 1000
        display_update(status, 0, 0, 0, uptime)
        client = None
        while client is None:
            time.sleep(5)
            try:
                client = mqtt_connect()
            except Exception as e2:
                print("Reconnect fehlgeschlagen:", e2)