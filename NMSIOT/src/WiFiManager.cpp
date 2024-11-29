#include "WiFiManager.h"

Preferences preferences;
AsyncWebServer server(80);
const char *AP_SSID = "ESP32-Config";
const char *AP_PASSWORD = "12345678";
unsigned long lastRetryTime = 0;
unsigned long apRetryTime = 0;
int retryCount = 0;

void InitWiFi() {
  preferences.begin("wifi-config", true);
  String ssid = preferences.getString("ssid", "");
  String password = preferences.getString("password", "");
  preferences.end();

  if (ssid.isEmpty()) {
    Serial.println("No saved WiFi credentials found. Starting AP mode...");
    startAPMode();
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());
  Serial.printf("Connecting to SSID: %s\n", ssid.c_str());

  retryCount = 0;
  lastRetryTime = millis();

  while (retryCount < MAX_RETRIES) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("WiFi connected successfully!");
      Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
      return;
    }

    if (millis() - lastRetryTime > RETRY_INTERVAL) {
      retryCount++;
      Serial.printf("Retrying WiFi connection (%d/%d)...\n", retryCount, MAX_RETRIES);
      lastRetryTime = millis();
    }

    delay(10);  // Non-blocking delay
  }

  Serial.println("WiFi connection failed. Switching to AP mode...");
  startAPMode();
}

const bool reconnect() {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }
  if (WiFi.status() != WL_CONNECTED && !WiFi.softAPgetStationNum()) {
    if (millis() - apRetryTime > AP_RETRY_INTERVAL) {
      Serial.println("Retrying WiFi connection ...");
      InitWiFi();
      apRetryTime = millis();
    }
  }
  return false;
}

void startAPMode() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  Serial.printf("AP Mode started with SSID: %s\n", AP_SSID);
  Serial.printf("Access the configuration page at: http://192.168.4.1\n");

  // Start configuration server
  startConfigServer();
}

void startConfigServer() {
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(200, "text/html",
                  R"rawliteral(
<!DOCTYPE html>
<html>
<head><title>WiFi Config</title></head>
<body>
<h1>Configure WiFi</h1>
<form action="/setwifi" method="POST">
  SSID: <input type="text" name="ssid"><br>
  Password: <input type="password" name="password"><br>
  <input type="submit" value="Save">
</form>
</body>
</html>
)rawliteral");
  });

  server.on("/setwifi", HTTP_POST, [](AsyncWebServerRequest *request) {
    if (!request->hasParam("ssid", true) || !request->hasParam("password", true)) {
      request->send(400, "text/plain", "Invalid parameters!");
      return;
    }

    String ssid = request->getParam("ssid", true)->value();
    String password = request->getParam("password", true)->value();

    saveWiFiCredentials(ssid.c_str(), password.c_str());

    request->send(200, "text/plain", "Credentials saved! Restarting...");
    delay(2000);  // Ensure the response is sent before restarting
    ESP.restart();
  });

  server.begin();
  Serial.println("Configuration server started.");
}

void saveWiFiCredentials(const char *ssid, const char *password) {
  preferences.begin("wifi-config", false);
  preferences.putString("ssid", ssid);
  preferences.putString("password", password);
  preferences.end();
  Serial.println("WiFi credentials saved.");
}
