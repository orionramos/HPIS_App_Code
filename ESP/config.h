#ifndef __CONFG_H___
#define __CONFG_H___

/* Pins definitions */
#define LED_PIN                     4
#define BTN_PIN                     5

/* Communication params */
#define ACK                         "A" // acknowledgment packet
#define QUEUE_LEN                   5
#define MAX_BUFFER_LEN              128

/* WiFi params */
#define WIFI_SSID                   "ESP32"
#define WIFI_PASSWORD               "Esp32-123"

/* Socket */
#define SERVER_ADDRESS              "192.168.4.2"
#define SERVER_PORT                 7890

#endif // __CONFG_H___