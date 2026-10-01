#include <WiFi.h>
#include <PubSubClient.h>
#include <math.h> // Library untuk fungsi log() matematika Steinhart-Hart

// ================= CONFIGURATION =================
// Konfigurasi Jaringan
const char* ssid     = "ST-X13";
const char* password = "st13p57m36";

// Konfigurasi MQTT Broker Lokal (Mosquitto Linux)
const char* mqtt_server = "192.168.1.13"; // Sesuaikan dengan IP Linux Anda
const int mqtt_port    = 1883;
const char* mqtt_topic  = "cinfarm/device/esp-farm-1/data";

// Konfigurasi Pin & Karakteristik Thermistor NTC
#define THERMISTORPIN 34         // Sensor dicolok ke pin analog 34
#define SERIESRESISTOR 10000     // Resistor pembagi Anda (10k Ohm)
#define NOMINAL_RESISTANCE 10000 // Nilai hambatan sensor NTC pada 25C (10k)
#define NOMINAL_TEMPERATURE 25   // Suhu ruangan standar (25C)
#define BCOEFFICIENT 3950        // Karakteristik beta sensor NTC (standar 3950)

// Jeda Pengiriman Data dan Pembacaan Sensor (Setiap 5 detik)
unsigned long lastMsg = 0;
#define MSG_INTERVAL 5000 
// =================================================

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Menghubungkan ke ");
    Serial.println(ssid);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nWiFi Terhubung!");
}

void reconnect() {
    while (!client.connected()) {
        Serial.print("Mencoba koneksi ke Mosquitto Linux...");
        String clientId = "ESP32_Cinfarm_Node1";
        
        if (client.connect(clientId.c_str())) {
            Serial.println("Terhubung ke Broker Mosquitto!");
        } else {
            Serial.print("Gagal, rc=");
            Serial.print(client.state());
            Serial.println(" Coba lagi dalam 5 detik...");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200); // Kecepatan disamakan ke 115200 untuk ESP32
    setup_wifi();
    
    // Inisialisasi MQTT
    client.setServer(mqtt_server, mqtt_port);
    
    // Konfigurasi resolusi ADC ESP32 (Default 12-bit / 4095)
    analogReadResolution(12);
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop(); // Wajib berjalan lancar tanpa terhambat delay()

    unsigned long now = millis();
    if (now - lastMsg > MSG_INTERVAL) {
        lastMsg = now;

        // 1. Ambil data analog dari ESP32
        float analogVal = analogRead(THERMISTORPIN);
        
        // Cek pengaman agar tidak terjadi pembagian dengan nol
        if (analogVal == 0) analogVal = 1; 

        // 2. Hitung nilai resistansi NTC saat ini
        float resistance = SERIESRESISTOR * (4095.0 / analogVal - 1.0);
       
        // 3. Rumus Steinhart-Hart (Mengubah hambatan ke Celsius)
        float steinhart;
        steinhart = resistance / NOMINAL_RESISTANCE;       // (R/Ro)
        steinhart = log(steinhart);                        // ln(R/Ro)
        steinhart /= BCOEFFICIENT;                         // 1/B * ln(R/Ro)
        steinhart += 1.0 / (NOMINAL_TEMPERATURE + 273.15); // + (1/To)
        steinhart = 1.0 / steinhart;                       // Balikkan nilai
        float tempC = steinhart - 273.15;                  // Konversi ke Celsius
       
        // Tampilkan hasil pembacaan ke Serial Monitor lokal
        Serial.print("Suhu Air Kolam Ikan: ");
        Serial.print(tempC);
        Serial.println(" *C");

        // 4. Konversi float ke string temporary terlebih dahulu
        char tempStr[8];
        dtostrf(tempC, 4, 2, tempStr);

        // 5. Bungkus string suhu ke dalam format JSON objek {"temp": xx.xx}
        char payload[32];
        snprintf(payload, sizeof(payload), "{\"temp\":%s}", tempStr);

        // 6. Kirim data ke Mosquitto Broker Linux
        Serial.print("Kirim JSON ke Mosquitto: ");
        Serial.println(payload);
        client.publish(mqtt_topic, payload);
    }
}
