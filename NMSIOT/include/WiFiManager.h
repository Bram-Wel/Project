#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <Preferences.h>

void InitWiFi();
const bool reconnect();
void startAPMode();
void startConfigServer();
void saveWiFiCredentials(const char *ssid, const char *password);

extern Preferences preferences;
extern AsyncWebServer server;
extern const char *AP_SSID;
extern const char *AP_PASSWORD;
extern unsigned long lastRetryTime;
extern unsigned long apRetryTime;
extern int retryCount;

#define MAX_RETRIES 5
#define RETRY_INTERVAL 2000
#define AP_RETRY_INTERVAL 60000

#endif // WIFI_MANAGER_H
