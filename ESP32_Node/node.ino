#include <Wire.h>
#include <LoRa_E220.h>
#include <TinyGPS++.h>
#include <Adafruit_BMP280.h>
#include <Adafruit_AHTX0.h>
#include "esp_sleep.h"

// ================= IDENTITAS =================
const String NODE_ID = "Node_01";

// ================= PIN =================
#define LORA_RX 16
#define LORA_TX 17
#define LORA_AUX 4
#define BUTTON_PIN 25
#define BUZZER_PIN 13
#define LED_PIN 12
#define RAIN_PIN 34
#define GPS_RX 26
#define GPS_TX 27

// ================= OBJECT =================
LoRa_E220 e220(&Serial2, LORA_AUX);
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);
Adafruit_BMP280 bmp;
Adafruit_AHTX0 aht;

// ================= STATUS =================
bool bmp_ok = false;
bool aht_ok = false;

// ================= DEEP SLEEP =================
#define uS_TO_S_FACTOR 1000000
#define TIME_TO_SLEEP 300 // 5 menit

// ================= FUNCTION =================
void sendData(int emergency, bool useGPS);
void waitFeedback();
void goToSleep();

void setup() {
  Serial.begin(115200);
  delay(500);

  esp_sleep_wakeup_cause_t wakeReason = esp_sleep_get_wakeup_cause();
  Serial.println("=== SYSTEM WAKE ===");

  // ===== INIT =====
  Serial2.begin(9600, SERIAL_8N1, LORA_RX, LORA_TX);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(LORA_AUX, INPUT);
  
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  Wire.begin(21, 22);
  Wire.setClock(100000);
  delay(200);

  // ===== SENSOR =====
  if (bmp.begin(0x76) || bmp.begin(0x77)) bmp_ok = true;
  else Serial.println("BMP280 ERROR");

  if (aht.begin()) aht_ok = true;
  else Serial.println("AHT20 ERROR");

  e220.begin();

  // ===== MODE =====
  if (wakeReason == ESP_SLEEP_WAKEUP_EXT0) {
    Serial.println("MODE: EMERGENCY");
    
    // Indikator Transmit Awal Fisik
    digitalWrite(LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);

    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      digitalWrite(LED_PIN, HIGH);
      delay(150);
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      delay(150);
    }

    // Kirim data SOS ke Basecamp
    sendData(1, true);

    // SOLUSI A: Menunggu Konfirmasi Balasan Instan berbasis Teks Murni
    waitFeedback();

  } else {
    Serial.println("MODE: NORMAL");
    int rainValue = analogRead(RAIN_PIN);
    bool rainDetected = (rainValue < 2500);

    if (rainDetected) {
      Serial.println("RAIN DETECTED -> SEND");
      sendData(1, false);
      waitFeedback(); 
    } else {
      sendData(0, false);
    }
  }

  goToSleep();
}

void loop() {
  // tidak digunakan
}

// ================= SEND DATA =================
void sendData(int emergency, bool useGPS) {
  sensors_event_t humidity, temp;
  if (aht_ok) aht.getEvent(&humidity, &temp);
  else {
    temp.temperature = 0;
    humidity.relative_humidity = 0;
  }

  float pressure = 0.0;
  if (bmp_ok) {
    pressure = bmp.readPressure() / 100.0F;
    if (isnan(pressure) || pressure < 300 || pressure > 1100) {
      pressure = 0.0;
    }
  }

  int rainValue = analogRead(RAIN_PIN);
  double lat = -7.115679;
  double lon = 112.427924;

  if (useGPS) {
    unsigned long start = millis();
    while (millis() - start < 8000) {
      while (gpsSerial.available()) {
        gps.encode(gpsSerial.read());
      }
    }

    if (gps.location.isValid() && gps.location.lat() != 0) {
      lat = gps.location.lat();
      lon = gps.location.lng();
    }
  }

  // ===== PAYLOAD =====
  String payload = NODE_ID + "," +
                   String(lat, 6) + "," +
                   String(lon, 6) + "," +
                   String(rainValue) + "," +
                   String(temp.temperature, 1) + "," +
                   String(humidity.relative_humidity, 1) + "," +
                   String(pressure, 1) + "," +
                   String(emergency);
                   
  e220.sendMessage(payload);

  Serial.println("SEND:");
  Serial.println(payload);

  // Amankan siklus transmisi radio udara via pin AUX sebelum mendengarkan balik
  delay(20);
  while (digitalRead(LORA_AUX) == LOW) {
    delay(5);
  }
}

// ================= PERBAIKAN UTAMA SOLUSI A =================
void waitFeedback() {
  Serial.println("⏳ Menunggu Konfirmasi Sinyal Balik (ACK02) murni dari Basecamp...");
  unsigned long startWait = millis();
  bool ackReceived = false;

  // Membuka jendela pembacaan murni dari port serial LoRa (Serial2) selama 15 detik
  while (millis() - startWait < 15000) {
    if (Serial2.available() > 0) {
      // Membaca string murni sampai karakter ganti baris (\n) yang dikirim Python
      String msg = Serial2.readStringUntil('\n');
      msg.trim();

      if (msg == "ACK02") {
        Serial.println("🎯🎯 ACK02 BERHASIL DITERIMA SECARA DIREK MURNI!");
        ackReceived = true;
        
        // Pola Umpan Balik Sukses: Bunyikan buzzer dan nyalakan LED kedip panjang 5 kali cepat
        for (int i = 0; i < 5; i++) {
          digitalWrite(BUZZER_PIN, HIGH);
          digitalWrite(LED_PIN, HIGH);
          delay(400);
          digitalWrite(BUZZER_PIN, LOW);
          digitalWrite(LED_PIN, LOW);
          delay(150);
        }
        break; 
      }
    }
    delay(10); 
  }

  if (!ackReceived) {
    Serial.println("❌ Batas waktu habis. Gateway tidak mengirimkan sinyal balik.");
  }
}

// ================= SLEEP =================
void goToSleep() {
  Serial.println("GOING TO SLEEP...");
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * uS_TO_S_FACTOR);
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_25, 0);

  delay(200);
  esp_deep_sleep_start();
}
