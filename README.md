# Emergency Communication System in Mountain Hiking Areas Using IoT and LoRa

Final Project

D3 Informatics Engineering

Politeknik Elektronika Negeri Surabaya (PENS)

---

## Overview

This project develops an emergency communication system designed for mountain hiking areas where cellular communication is unavailable.

The system utilizes LoRa communication between a portable node carried by hikers and a gateway located at the basecamp. Information received by the gateway is forwarded through MQTT and displayed in Home Assistant for real-time monitoring.

---

## Background

Mountain hiking areas frequently experience limited or no cellular network coverage. During emergency situations such as accidents or hikers getting lost, communication with rescuers becomes difficult.

This project provides an alternative communication system capable of operating independently from cellular or internet infrastructure.

---

## Main Features

✔ GPS Tracking

✔ Emergency SOS Button

✔ LoRa Long Range Communication

✔ Raspberry Pi Gateway

✔ MQTT Communication

✔ Home Assistant Dashboard

✔ Environmental Monitoring

✔ OLED Display

✔ Deep Sleep Power Saving

✔ Solar Charging System

---

## System Architecture

```
GPS
        │
BME280 Sensor
        │
 SOS Button
        │
     ESP32
        │
   LoRa E220
        │
~~~~~~~~~~~~~~~
  LoRa Wireless
~~~~~~~~~~~~~~~
        │
 Raspberry Pi
        │
 MQTT Broker
        │
Home Assistant
```

---

## Hardware Specification

### Node

- ESP32
- EByte E220 LoRa
- GPS NEO-6M
- BME280
- OLED SSD1306
- SOS Push Button
- 18650 Battery
- CN3791 MPPT
- Solar Panel 6V 3W

---

### Gateway

- Raspberry Pi
- EByte E220 LoRa
- OLED SSD1306
- Active Buzzer
- MQTT Broker
- Home Assistant

---

## Software

Arduino IDE

Python 3

Raspberry Pi OS

Home Assistant

Mosquitto MQTT Broker

---

## Folder Structure

ESP32_Node

Arduino source code.

RaspberryPi_Gateway

Gateway application.

HomeAssistant

Dashboard configuration.

Documentation

Project documentation.

Tutorial

Installation guide.

---

## Installation

### ESP32

Open

```
ESP32_Node/Node.ino
```

Compile and upload using Arduino IDE.

---

### Raspberry Pi

Clone repository

```bash
git clone https://github.com/YOUR_USERNAME/Emergency-Communication-IoT-LoRa.git
```

Go to folder

```bash
cd Emergency-Communication-IoT-LoRa/RaspberryPi_Gateway
```

Install dependency

```bash
pip3 install -r requirements.txt
```

Run gateway

```bash
python3 gateway.py
```

Or using systemd

```bash
sudo systemctl enable gateway.service
sudo systemctl start gateway.service
```

---

## MQTT

Default Broker

```
103.106.72.181
```

Communication Topic

```
home/nodes/Node_01
```

---

## Test Parameters

GPS Accuracy

GPS Movement

RSSI

Latency

Packet Delivery Ratio

Deep Sleep

Solar Charging

---

## Results

The developed system successfully

- sends GPS coordinates

- sends environmental sensor data

- transmits emergency SOS messages

- performs two-way LoRa communication

- displays real-time monitoring on Home Assistant

- operates using solar-powered energy

---

## Future Development

- Mesh Networking

- End-to-End Encryption

- Adaptive Deep Sleep

- Weather Information Integration

- Multiple Emergency Alert Pattern

---

## Author

Rifky Ammar Sidiq

D3 Informatics Engineering

Politeknik Elektronika Negeri Surabaya

2026
