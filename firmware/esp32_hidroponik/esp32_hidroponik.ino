#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <vector>
#include <NTPClient.h>
#include <WiFiClientSecure.h>
#include <set> 
#include <map>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <DHT11.h>

#include <OneWire.h>
#include <DallasTemperature.h>


#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensorSuhu(&oneWire);

#define TdsSensorPin 34        // Gunakan pin ADC di ESP32, contoh: GPIO34
#define VREF 3.3               // Referensi tegangan ADC di ESP32
#define SCOUNT 30              // Jumlah sampel

int analogBuffer[SCOUNT];
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;
int copyIndex = 0;

float averageVoltage = 0;
float tdsValue = 0;
float temperature = 25;        // Suhu air untuk kompensasi

#define DHTPIN 4  
DHT11 dht11(DHTPIN);

#define PIN_SUHU_AIR    13
#define PIN_TDS         27
#define PIN_DEBIT       26
#define PIN_LEVEL_AIR   25

// --- Konfigurasi PIN ---
#define PIN_DEBIT     14
#define PIN_SUHU_AIR  4
uint8_t pinSensor[1] = {32};
bool warningSensor[1] = { false };
uint8_t valueSensor[1] = { 0 };

// --- Konfigurasi WiFi & Server ---
const char* ssid = "Banyak makan";   
const char* password = "rhevan1119"; 
// const char* ssid = "CINIoTFarm";
// const char* password = "CINFarmIoT123";
const char* serverUrl_get  = "http://orangepi.local:3000/api/data-get?file=hidroponik"; 
const char* serverUrl_post = "http://orangepi.local:3000/api/data-post?file=hidroponik"; 

// --- NTP Time ---
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "time.google.com", 3600 * 7, 60000);  // GMT+7

// --- Struktur Alarm ---
struct Alarm {
  int hari; // -1 = setiap hari
  int pin;
  int jam_N, menit_N, detik_N;
  int jam_L, menit_L, detik_L;
  std::vector<int> pengecualianHari;
  String deskripsi;
};

std::vector<Alarm> alarms;

std::set<int> initializedPins;

SemaphoreHandle_t xAlarmMutex = NULL;

// Median filtering
int getMedianNum(int bArray[], int iFilterLen) {
  int bTab[iFilterLen];
  for (byte i = 0; i < iFilterLen; i++)
    bTab[i] = bArray[i];
  
  int i, j, bTemp;
  for (j = 0; j < iFilterLen - 1; j++) {
    for (i = 0; i < iFilterLen - j - 1; i++) {
      if (bTab[i] > bTab[i + 1]) {
        bTemp = bTab[i];
        bTab[i] = bTab[i + 1];
        bTab[i + 1] = bTemp;
      }
    }
  }
  if ((iFilterLen & 1) > 0) {
    bTemp = bTab[(iFilterLen - 1) / 2];
  } else {
    bTemp = (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
  }
  return bTemp;
}

float ambilSuhu()

{

sensorSuhu.requestTemperatures();

float suhu = sensorSuhu.getTempCByIndex(0);

return suhu;

}

int8_t convertHariToInt(const String& hari) {
  if (hari == "Minggu") return 0;
  if (hari == "Senin") return 1;
  if (hari == "Selasa") return 2;
  if (hari == "Rabu") return 3;
  if (hari == "Kamis") return 4;
  if (hari == "Jumat") return 5;
  if (hari == "Sabtu") return 6;
  return -1;
}

void parseTimeFull(const String& timeStr, int& jam, int& menit, int& detik) {
  sscanf(timeStr.c_str(), "%d:%d:%d", &jam, &menit, &detik);
}


/*================================LOAD FROM JSON==============================*/
void safeLoadAlarms(JsonDocument& doc) {
  if (xSemaphoreTake(xAlarmMutex, portMAX_DELAY)) {
    alarms.clear();

    const char* jenisIkan[1] = {"plantInfo"};

    for (int i = 0; i < 1; i++) {
      if (!doc.containsKey(jenisIkan[i])) continue;
      JsonArray array = doc[jenisIkan[i]]["jadwal"].as<JsonArray>();

      for (JsonObject obj : array) {
        Alarm a;
        String hariStr = obj["hari"] | "";
        a.hari = (hariStr == "Setiap Hari") ? -1 : convertHariToInt(hariStr);
        a.pin = obj["pin"].as<int>();
        a.deskripsi = obj["deskripsi"].as<const char*>();

        // Pengecualian hanya digunakan jika Setiap Hari
        a.pengecualianHari.clear();
        if (a.hari == -1 && obj.containsKey("pengecualian")) {
          JsonArray pArray = obj["pengecualian"].as<JsonArray>();
          for (const auto& hariEx : pArray) {
            int8_t hariExInt = convertHariToInt(hariEx.as<String>());
            if (hariExInt >= 0) {
              a.pengecualianHari.push_back(hariExInt);
            }
          }
        }

        // Parsing waktu
        String start = obj["start"] | "00:00:00";
        String end   = obj["end"] | "00:00:00";
        parseTimeFull(start, a.jam_N, a.menit_N, a.detik_N);
        parseTimeFull(end, a.jam_L, a.menit_L, a.detik_L);

        // Set pinMode hanya jika belum
        if (!initializedPins.count(a.pin)) {
          pinMode(a.pin, OUTPUT);
          digitalWrite(a.pin, HIGH);  // Pastikan relay OFF awalnya
          initializedPins.insert(a.pin);
        }

        alarms.push_back(a);
      }
    }

    xSemaphoreGive(xAlarmMutex);
  }
}

/*================================CHECK ALARM================================*/

void checkAndRunAlarms() {
  uint8_t jam   = timeClient.getHours();
  uint8_t menit = timeClient.getMinutes();
  uint8_t detik = timeClient.getSeconds();

  time_t rawTime = (time_t)timeClient.getEpochTime();
  struct tm *ptm = localtime(&rawTime);
  uint8_t currentDay = ptm->tm_wday; // 0 = Minggu, ..., 6 = Sabtu

  int nowSeconds = jam * 3600 + menit * 60 + detik;

  //Serial.printf("⏰ Sekarang: %02d:%02d:%02d | Hari: %d\n", jam, menit, detik, currentDay);

  // Map untuk menyimpan status akhir setiap pin
  std::map<uint8_t, bool> pinHarusAktif; // true = ON (LOW), false = OFF (HIGH)

  for (auto& a : alarms) {
    bool aktifHariIni = false;

    if (a.hari == -1) {
      if (std::find(a.pengecualianHari.begin(), a.pengecualianHari.end(), currentDay) == a.pengecualianHari.end()) {
        aktifHariIni = true;
      }
    } else {
      aktifHariIni = (a.hari == currentDay);
    }

    if (!aktifHariIni) {
      continue; // Lewati alarm yang tidak aktif hari ini
    }

    int onTime  = a.jam_N * 3600 + a.menit_N * 60 + a.detik_N;
    int offTime = a.jam_L * 3600 + a.menit_L * 60 + a.detik_L;

    bool isActive = false;
    if (onTime <= offTime) {
      isActive = nowSeconds >= onTime && nowSeconds < offTime;
    } else {
      isActive = nowSeconds >= onTime || nowSeconds < offTime;
    }

    if (isActive) {
      pinHarusAktif[a.pin] = true; // Catat bahwa pin ini harus ON
      //Serial.printf("✅ Alarm pin %d AKTIF sekarang (%02d:%02d:%02d - %02d:%02d:%02d)\n",a.pin, a.jam_N, a.menit_N, a.detik_N, a.jam_L, a.menit_L, a.detik_L);
    } else {
      // Hanya tandai OFF jika belum ada yang aktif
      if (pinHarusAktif.find(a.pin) == pinHarusAktif.end()) {
        pinHarusAktif[a.pin] = false;
        // Serial.printf("🛑 Alarm pin %d TIDAK AKTIF sekarang (di luar waktu %02d:%02d:%02d - %02d:%02d:%02d)\n",a.pin, a.jam_N, a.menit_N, a.detik_N, a.jam_L, a.menit_L, a.detik_L);
      }
    }
  }

  // Terapkan status akhir ke masing-masing pin
  for (const auto& status : pinHarusAktif) {
    digitalWrite(status.first, status.second ? LOW : HIGH); // LOW = ON, HIGH = OFF
  }
}


// Tambahkan di bagian global (di luar fungsi dataPost)
static unsigned long analogSampleTimepoint = 0;
static unsigned long printTimepoint = 0;

/*================================DATA POST===================================*/
bool dataPost() {
  if (WiFi.status() != WL_CONNECTED) return false;

  WiFiClient client;
  HTTPClient http;
  http.setTimeout(3000);
  http.begin(client, serverUrl_post);
  http.addHeader("Content-Type", "application/json");

    int suhu_udara = 0;
    int kelembapan_udara = 0;

    // Attempt to read the temperature and humidity values from the DHT11 sensor.
    int result = dht11.readTemperatureHumidity(suhu_udara, kelembapan_udara);

    // Check the results of the readings.
    // If the reading is successful, print the temperature and humidity values.
    // If there are errors, print the appropriate error messages.
    if (result != 0) {
      int suhu_udara = 0;
      int kelembapan_udara = 0;
      Serial.println(DHT11::getErrorString(result));
    } 

  if (millis() - analogSampleTimepoint > 40U) { // setiap 40 ms baca ADC
    analogSampleTimepoint = millis();
    analogBuffer[analogBufferIndex] = analogRead(TdsSensorPin);
    analogBufferIndex++;
    if (analogBufferIndex == SCOUNT) {
      analogBufferIndex = 0;
    }
  }

if (millis() - printTimepoint > 800U) { // setiap 800 ms proses data
    printTimepoint = millis();

    // Salin data buffer
    for (copyIndex = 0; copyIndex < SCOUNT; copyIndex++) {
        analogBufferTemp[copyIndex] = analogBuffer[copyIndex];
    }

    // Median filter → konversi ke volt
    int rawADC = getMedianNum(analogBufferTemp, SCOUNT);
    averageVoltage = rawADC * (float)VREF / 4095.0;

    // Kompensasi suhu (pakai default kalau belum ada sensor suhu)
    if (temperature <= 0) temperature = 25.0; 
    float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
    float compensationVoltage = averageVoltage / compensationCoefficient;

    // Hitung TDS
    tdsValue = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage
                - 255.86 * compensationVoltage * compensationVoltage
                + 857.39 * compensationVoltage) * 0.5;

    // --- DEBUG ---
    Serial.print("Raw ADC: ");
    Serial.print(rawADC);
    Serial.print(" | Avg Voltage: ");
    Serial.print(averageVoltage, 3);
    Serial.print(" V | Comp Voltage: ");
    Serial.print(compensationVoltage, 3);
    Serial.print(" V | TDS: ");
    Serial.print(tdsValue, 0);
    Serial.println(" ppm");
}


  uint8_t status = 1;
  uint8_t temperature = 25; //ambilSuhu();
  float debit = 0;
  uint8_t level_air = 0;

  String jsonData = "{";
  jsonData += "\"HidroponikInfo\":{";
  jsonData += "\"status\":" + String(status) + ",";
  jsonData += "\"suhu_air\":" + String(temperature) + ",";
  jsonData += "\"tds\":" + String(tdsValue) + ",";
  jsonData += "\"debit\":" + String(debit, 2) + ",";
  jsonData += "\"suhu_udara\":" + String(suhu_udara) + ",";
  jsonData += "\"kelembapan_udara\":" + String(kelembapan_udara) + ",";
  jsonData += "\"level_air\":" + String(level_air);
  jsonData += "}}";

  int httpResponseCode = http.POST(jsonData);

  if (httpResponseCode > 0) {
    String response = http.getString();
    //Serial.println("(POST)-> " + response);
    http.end();
    return true;
  } else {
    //Serial.println("(ERROR_POST)-> " + String(httpResponseCode));
    http.end();
    return false;
  }
}

/*================================DATA GET===================================*/
bool dataGet() {
  if (WiFi.status() != WL_CONNECTED) return false;

  WiFiClient client;
  HTTPClient http;
  http.setTimeout(3000);
  http.begin(client, serverUrl_get);

  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();

    DynamicJsonDocument doc(2048);
    DeserializationError error = deserializeJson(doc, payload);

    if (error) {
      Serial.println("JSON parsing failed!");
      http.end();
      return false;
    }

    String snapDoc = doc["plantInfo"]["jadwal"].as<String>();
    static String lastDoc = "";

    if (doc != lastDoc) {
      safeLoadAlarms(doc);
      lastDoc = snapDoc;
    }

    Serial.println("(GET)-> " + String(httpCode));
    http.end();
    return true;
  } else {
    Serial.println("(ERROR_GET)-> " + String(httpCode));
    http.end();
    return false; 
  }
}

// --- Task: Data GET every 5s ---
void TaskDataGet(void * pvParameters) {
  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xInterval = 15000 / portTICK_PERIOD_MS; // 5 detik

  while (true) {
    if (!dataGet()) Serial.println("(ERROR_GET)-> -1");
    vTaskDelayUntil(&xLastWakeTime, xInterval);
  }
}

// --- Task: Data POST every 5s ---
void TaskDataPost(void * pvParameters) {
  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xInterval = 60000 / portTICK_PERIOD_MS;

  while (true) {
    if (!dataPost()) Serial.println("(ERROR_POST)-> -1");
    vTaskDelayUntil(&xLastWakeTime, xInterval);
  }
}

// --- Task: Check alarms every 1s ---
void TaskCheckAlarms(void * pvParameters) {
  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xInterval = 1000 / portTICK_PERIOD_MS;

  while (true) {
    if (xSemaphoreTake(xAlarmMutex, 50 / portTICK_PERIOD_MS)) {
      checkAndRunAlarms();
      xSemaphoreGive(xAlarmMutex);
    }
    vTaskDelayUntil(&xLastWakeTime, xInterval);
  }
}


void TaskWiFiMonitor(void* pvParameters) {
  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xInterval = 10000 / portTICK_PERIOD_MS; // cek tiap 10 detik

  static int retryCount = 0;
  const int maxRetry = 10;

  for (;;) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("⚠️ WiFi Lost");

      if (retryCount == 0) {
        Serial.println("🔄 Disconnect dulu dan mulai konek ulang");
        WiFi.disconnect(true);
      }

      Serial.printf("⏳ Reconnect try %d/%d\n", retryCount + 1, maxRetry);
      WiFi.begin(ssid, password);  // panggil tiap retry supaya konek ulang

      retryCount++;

      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("✅ WiFi Reconnected!");
        retryCount = 0; // reset retry
      } else if (retryCount >= maxRetry) {
        Serial.println("❌ Max retry reached, tunggu siklus berikutnya");
        retryCount = 0; // reset retry
      }
    } else {
      retryCount = 0; // reset jika sudah connected
    }

    vTaskDelayUntil(&xLastWakeTime, xInterval);
  }
}

void syncTime(void* pvParameters) {
  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xInterval = 60000 / portTICK_PERIOD_MS;

  while (true) {
    timeClient.update();
    vTaskDelayUntil(&xLastWakeTime, xInterval);
  }
}
void setup() {
  Serial.begin(115200);

  pinMode(PIN_SUHU_AIR, INPUT);
  pinMode(PIN_DEBIT, INPUT);
  for (uint8_t i = 0; i < 6; i++) pinMode(pinSensor[i], INPUT);

  sensorSuhu.begin();

  WiFi.begin(ssid, password);
  Serial.print("🔌 Menghubungkan ke WiFi");
  int attempt = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
    if (++attempt > 20) {
      Serial.println("❌ Gagal konek WiFi");
      return;
    }
  }
  Serial.println("\n✅ WiFi terhubung");

  xAlarmMutex = xSemaphoreCreateMutex();
  if (xAlarmMutex == NULL) {
    Serial.println("❌ Gagal membuat mutex!");
    while (true); // berhenti agar tidak crash
  }


  timeClient.begin();
  delay(500);
  dataGet();
  dataPost();

  xTaskCreatePinnedToCore(TaskDataGet, "TaskDataGet", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(TaskDataPost, "TaskDataPost", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(TaskCheckAlarms, "TaskCheckAlarms", 6144, NULL, 2, NULL, 0);
  xTaskCreatePinnedToCore(TaskWiFiMonitor, "TaskWiFiMonitor", 2048, NULL, 0, NULL, 1);
  xTaskCreatePinnedToCore(syncTime, "syncTime", 2048, NULL, 0, NULL, 1);
}

void loop() {
  vTaskDelay(portMAX_DELAY); 
}