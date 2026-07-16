import serial
import paho.mqtt.client as mqtt
import json
import time
import threading
import socket
import RPi.GPIO as GPIO

# Import library untuk layar OLED I2C
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

# ================= CONFIG =================
MQTT_HOST = "103.106.72.181"
MQTT_PORT = 1883
MQTT_USER = "MEDLOC"
MQTT_PASS = "MEDLOC"

SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUDRATE = 9600

BUZZER_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# ================= GLOBAL VARIABLES =================
mqtt_status_text = "WAIT"
last_node_rx = "-"
last_time_rx = "-"
sos_is_active = False
device = None
ser = None

# ================= HELPER FUNCTIONS =================
def get_ip_address():
    """Mengambil IP Address lokal Raspberry Pi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_cpu_temp():
    """Membaca suhu internal prosesor Raspberry Pi"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
        return f"{temp:.1f}"
    except:
        return "--"

PI_IP_ADDRESS = get_ip_address()

# ================= OLED SETUP =================
try:
    serial_i2c = i2c(port=1, address=0x3C)
    device = ssd1306(serial_i2c)
    print("✅ Layar OLED 0.96 Inch Berhasil Diinisialisasi.")
except Exception as oled_err:
    print(f"❌ Gagal membuka layar OLED: {oled_err}")
    device = None

# ================= OLED DISPLAY FUNCTIONS =================
def update_oled_normal():
    """Menampilkan status kesehatan sistem di OLED saat normal"""
    if device and not sos_is_active:
        current_time = time.strftime("%H:%M:%S")
        cpu_temp = get_cpu_temp()
        with canvas(device) as draw:
            draw.text((0, 0), "=== GATEWAY STATS ===", fill="white")
            draw.text((0, 16), f"IP : {PI_IP_ADDRESS}", fill="white")
            draw.text((0, 28), f"MQT: {mqtt_status_text}", fill="white")
            draw.text((0, 40), f"Pi: {cpu_temp}C", fill="white")
            draw.text((0, 54), f"Time: {last_time_rx} ({current_time})", fill="white")

def update_oled_sos(node, lat, lon):
    """Menampilkan status darurat merah di OLED"""
    if device:
        with canvas(device) as draw:
            draw.text((0, 0), "! ! ! S O S ! ! !", fill="white")
            draw.text((0, 16), f"DARI : {node}", fill="white")
            draw.text((0, 28), f"LAT  : {lat}", fill="white")
            draw.text((0, 40), f"LON  : {lon}", fill="white")
            draw.text((0, 54), "EVAKUASI SEGERA!!", fill="white")

# ================= BUZZER =================
def buzzer_logic():
    """Fungsi alarm 30 detik yang berjalan di background"""
    global sos_is_active
    sos_is_active = True
    print("🚨 SOS AKTIF: Buzzer berbunyi selama 30 detik...")

    end_time = time.time() + 30
    while time.time() < end_time:
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(0.5)

    sos_is_active = False
    print("✅ Buzzer Off Otomatis (Timeout). Layar kembali normal.")
    update_oled_normal()

# ================= MQTT SETUP =================
def on_connect(client, userdata, flags, rc, properties=None):
    global mqtt_status_text
    if rc == 0:
        print("✅ TERHUBUNG ke Broker MQTT.")
        mqtt_status_text = "OK"
        client.subscribe("home/nodes/+/sos_reset")
    else:
        print(f"❌ GAGAL! Kode error: {rc}.")
        mqtt_status_text = "ERR"

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    global mqtt_status_text
    mqtt_status_text = "DC"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect = on_connect
client.on_disconnect = on_disconnect

try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"Tidak bisa terhubung ke server: {e}")
    mqtt_status_text = "ERR"

# ================= SERIAL SETUP =================
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=2)
    print("🚀 Gateway LoRa Aktif... Menunggu data...")
    update_oled_normal()
except Exception as e:
    print(f"❌ Gagal membuka Port Serial {SERIAL_PORT}: {e}")

# ================= MAIN LOOP =================
last_oled_refresh = time.time()

try:
    while True:
        # Refresh layar normal setiap 2 detik agar jam dan suhu CPU terus terupdate
        if not sos_is_active and (time.time() - last_oled_refresh > 2):
            update_oled_normal()
            last_oled_refresh = time.time()

        # Cek apakah ada data radio yang masuk
        if ser and ser.in_waiting > 0:
            raw_data = ser.readline()
            line = raw_data.decode('utf-8', errors='ignore').strip()

            if not line:
                continue

            if "Node_" in line:
                line = line[line.find("Node_"):]

            print(f"📩 Data Mentah Terproses: {line}")

            parts = line.split(',')
            if len(parts) == 8:
                try:
                    sos_status = int(parts[7])
                    node_id = parts[0]

                    lat_val = float(parts[1])
                    lon_val = float(parts[2])

                    # Simpan data terakhir untuk OLED Normal
                    last_node_rx = node_id
                    last_time_rx = time.strftime("%H:%M:%S")

                    payload = {
                        "node_id": node_id,
                        "latitude": lat_val,
                        "longitude": lon_val,
                        "rain": int(parts[3]),
                        "temp": float(parts[4]),
                        "humidity": float(parts[5]),
                        "pressure": parts[6],
                        "sos": sos_status
                    }

                    # Kirim ke Dashboard MQTT
                    topic = f"home/nodes/{node_id}"
                    client.publish(topic, json.dumps(payload))
                    print(f"📤 JSON Terkirim ke Topic: {topic}")

                    # LOGIKA SOS vs NORMAL
                    if sos_status == 1:
                        update_oled_sos(node_id, lat_val, lon_val)

                        if not sos_is_active:
                            threading.Thread(target=buzzer_logic, daemon=True).start()

                        print("📤 Mengirim balik sinyal ACK02 ke gunung...")
                        ser.write(b"ACK02\n")
                        ser.flush()
                        time.sleep(0.1)
                    else:
                        update_oled_normal()

                except Exception as parse_error:
                    print(f"❌ Gagal memproses data: {parse_error}")
            else:
                if len(line) > 0:
                    print(f"⚠️ Data diabaikan karena jumlah kolom tidak pas ({len(parts)}/8)")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n🛑 Mematikan Gateway...")

finally:
    GPIO.cleanup()
    client.loop_stop()
    if ser and ser.is_open:
        ser.close()
