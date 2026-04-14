import network, time, json
from machine import Pin, SPI
from umqtt.simple import MQTTClient
import st7789py as st7789
import vga2_16x32 as font

# --- WLAN ---
WLAN_SSID = "BZTG_local"
WLAN_PASS = "Mittelsenkrechte64"

"""
WLAN_SSID = "FRITZ!Box NB"
WLAN_PASS = "46914294587536504239"
"""

# MQTT KONFIGURATION
# Broker
MQTT_SERVER  = "10.12.168.18"
CLIENT_ID    = "Nils_ESP2"
BROKER_USER  = "NilsMQTT"
BROKER_PW    = "passwort"

# Topics für Daten und Status
TOPIC_WERTE  = "projekt/werte"
TOPIC_STATUS = "projekt/status"

# GLOBALE SYSTEMVARIABLEN
# Sensordaten werden über MQTT Topci werte aktualisiert
data = {"temp": 0, "humi": 0, "ligh": 0}

# Systemstatus (ONLINE / OFFLINE / UNKNOWN)1
# initial unbekannt
status = "UNKNOWN"

# Zeitmessung für Updates / Timeout / Anzeige
last_update = time.ticks_ms()
last_ping = time.ticks_ms()
start_time = time.ticks_ms()
last_msg_time = time.ticks_ms()

# Vergleichsvariable 
last_data = None

# WLAN FUNKTION

def wlan_verbinden(timeout=30):
    """
    Baut WLAN Verbindung auf.
    Wartend bis Verbindung steht oder Timeout =30s erreicht ist.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)          # WLAN reseten falls vorher aktiv war 
    time.sleep(0.5)
    wlan.active(True)
    wlan.connect(WLAN_SSID, WLAN_PASS)

    # Warten auf Verbindung
    for _ in range(timeout):
        if wlan.isconnected():
            #IP ausgeben
            print("Verbunden:", wlan.ifconfig()[0])
            return wlan
        print("Warten...")
        time.sleep(1)

    raise RuntimeError("Verbindungsaufbau WLAN fehlgeschlagen")

# WLAN initial starten 
wlan_verbinden()

# DISPLAY INITIALISIERUNG

spi = SPI(2, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(39), mosi=Pin(40))

# Rotationseinstellungen für Displayorientierung
custom_rotations = (
    (0x00, 170, 320, 35, 0, False),
    (0x60, 320, 170, 0, 35, False),
    (0xC0, 170, 320, 35, 0, False),
    (0xA0, 320, 170, 0, 35, False),
)

# Displayobjekt erzeugen (ST7789 Initialisierung)
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

# Display vorbereiten und eventuell vorhandene Daten nullen
tft.inversion_mode(True)
tft.fill(st7789.BLACK)

# Bildschirmpositionen für Textzeilen
x1 = 0
y1, y2, y3, y4, y5 = 0, 32, 64, 96, 128

# DISPLAY UPDATE FUNKTION

def display_update(status, temp, humi, ligh, uptime, since_last):
    """
    Aktualisiert das Display mit aktuellen Werten.
    Wird zyklisch im Loop aufgerufen.
    """
    #Status der Brokerverbindung
    tft.text(font, f"Status: {status}   ", x1, y1, st7789.WHITE,  st7789.BLACK)
    #Werte aus Topic projekt/werte
    tft.text(font, f"Temp: {temp}C    ", x1, y2, st7789.YELLOW, st7789.BLACK)
    tft.text(font, f"Humi: {humi}%    ", x1, y3, st7789.CYAN,   st7789.BLACK)
    tft.text(font, f"Ligh: {ligh}lux  ", x1, y4, st7789.YELLOW, st7789.BLACK)
    # Zeitinformationen: Laufzeit + Zeit seit letzter MQTT Nachricht
    tft.text(font, f"Time: {uptime}s Last: {since_last}s  ",x1, y5, st7789.WHITE, st7789.BLACK)

# MQTT CALLBACK (EINGEHENDE NACHRICHTEN)

def on_message(topic, msg):
    """
    Wird automatisch vom im Loop aufgerufen, sobald eine Nachricht auf einem abonnierten Topic ankommt.
    """
    global data, status, last_msg_time
    # Byte zu String Konvertierung
    topic = topic.decode()
    msg = msg.decode()

    # Zeitstempel aktualisieren (letzte MQTT Nachricht)
    last_msg_time = time.ticks_ms()

    # Sensordaten empfangen und ausgeben
    if topic == TOPIC_WERTE:
        try:
            data = json.loads(msg)
            #Debug-Ausgabe
            print("Empfangen:", data)
        #Fehlerbehandlung fehlerhaftes JSON Format
        except Exception as e:
            #Debug-Ausgabe
            print("JSON Fehler:", e, msg)

    # Statusverarbeitung (LWT / Online Status)

    elif topic == TOPIC_STATUS:
        if msg == "online":
            status = "ONLINE"
        elif msg == "offline":
            status = "OFFLINE (LWT)"
        else:
            status = "UNKNOWN"
        # Debug-Ausgabe für Rohdatenanalyse
        print("RAW STATUS:", repr(msg))
        print("Status:", status)

# MQTT VERBINDUNG

def mqtt_connect():
    """
    Baut MQTT Verbindung auf und registriert Callback.
    Abonnements für Topics werden hier gesetzt.
    """
    client = MQTTClient(
        CLIENT_ID,
        MQTT_SERVER,
        port=1883,
        user=BROKER_USER,
        password=BROKER_PW,
        keepalive=15
    )

    # Callback für eingehende Nachrichten registrieren
    client.set_callback(on_message)

    # Verbindung zum Broker herstellen
    client.connect(clean_session=True)

    # Topics abonnieren
    client.subscribe(TOPIC_WERTE)
    client.subscribe(TOPIC_STATUS)
    print("MQTT verbunden")
    return client

# RECONNECT FUNKTION

def reconnect():
    """
    Versucht MQTT neu zu verbinden.
    Wird aufgerufen wenn Client verloren geht.
    """
    global client
    try:
        client = mqtt_connect()
    except Exception as e:
        print("Reconnect fehlgeschlagen:", e)
        client = None

# Erster Verbindungsaufbau mit MQTT beim Start
client = mqtt_connect()

# Initiales Display-Update alle Werte nullen
display_update(status, 0, 0, 0, 0, 0)


# HAUPTSCHLEIFE

while True:
    try:
        # MQTT Verbindung prüfen
        if client is None:
            reconnect()
            time.sleep(2)
            continue
        # Prüft ob neue MQTT Nachrichten vorhanden sind
        client.check_msg()
        now = time.ticks_ms()
        # Display Update Logik
        current_snapshot = (status, data["temp"], data["humi"], data["ligh"])
        # Update nur wenn sich Werte ändern oder jede Sekunde
        if current_snapshot != last_data or time.ticks_diff(now, last_update) >= 1000:
            uptime = time.ticks_diff(now, start_time) // 1000
            since_last = time.ticks_diff(now, last_msg_time) // 1000
            
            # Display aktualisieren
            display_update(
                status,
                data["temp"],
                data["humi"],
                data["ligh"],
                uptime,
                since_last
            )
            last_data = current_snapshot
            last_update = now

    except OSError as e:
        # Fehlerbehandlung MQTT/WLAN
        import sys
        sys.print_exception(e)
        status = "ERROR"
        uptime = time.ticks_diff(time.ticks_ms(), start_time) // 1000
        # Notfallanzeige
        display_update(status, 0, 0, 0, uptime, 0)

        # MQTT Client verwerfen → Reconnect nötig
        client = None
        time.sleep(2)