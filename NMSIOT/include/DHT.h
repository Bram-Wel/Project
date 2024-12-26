#ifndef DHT_H
#define DHT_H

#include <DHTesp.h>
#include <Ticker.h>

// Function declarations
bool initTemp();
void triggerGetTemp();
void tempTask(void *pvParameters);
bool getTemperature();

// External variables
/** Flag if task should run */
extern bool tasksEnabled;
/** Task handle for the light value read task */
extern TaskHandle_t tempTaskHandle;
/** Comfort profile */
extern ComfortState cf;
/** Temperature and humidity values */
extern TempAndHumidity newValues;
/** Heat index */
extern float heatIndex;
/** Dew point */
extern float dewPoint;
/** Comfort ratio */
extern float cr;
/** Comfort status */
extern String comfortStatus;

#endif // DHT_H