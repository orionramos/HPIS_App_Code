#ifndef __CONFG_H___
#define __CONFG_H___

/* Pins definitions */
#define GT_PIN                     4 //Pin de salida para la prótesis
#define BTN_PIN                     5 //Pin de entrada EMG

/* WiFi params */
#define WIFI_SSID                   "ESP32" //Nombre de la red WIFI
#define WIFI_PASSWORD               "Esp32-123" //Clave de la red WIFI

/* Socket */
#define SERVER_ADDRESS              "192.168.4.2" //Ip WebSocketServer
#define SERVER_PORT                 7890 //Puerta WebSocketServer

#endif // __CONFG_H___