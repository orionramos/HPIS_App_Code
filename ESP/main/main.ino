#include "config.h"
#include "wifi_communicator.h"
#include <esp_wifi.h>
#include <WiFiUdp.h>
#include <esp_netif.h>
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_log.h"
#include <ESPping.h>
#include <ArduinoJson.h>
#include <ArduinoWebsockets.h>


//button values
int EMGA = 0;
int EMGB = 0;
int lastEMGA = 0;
int lastEMGB = 0;
int EMGA_counter = 0;
int EMGB_counter = 0;
int gripType = 0;
int lastGripType = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.mode(WIFI_AP);  //Define el tipo de conexión WIFI
  WiFi.softAP(WIFI_SSID, WIFI_PASSWORD); //Define el nombre de rede y la clave

  Serial.println("\nWiFi network established!");
  Serial.println(WiFi.softAPIP());

  //serverIPAdress = findServerIP();
  IPAddress ip (192, 168, 4, 2); // IP de el primer dispositivo conectado
  
  while (!Ping.ping(ip)) {
    Serial.println("!PING");
    delay(1000);
  }

  Serial.println("PING!"); //Dispositivo encontrado

  Serial.println(is_client_conected());

  pinMode(GT_PIN, OUTPUT); //Salida para la prótesis
  
  pinMode(EMGA_PIN, INPUT_PULLUP); //Simulador EMG
  pinMode(EMGB_PIN, INPUT_PULLUP); //Simulador EMG
}

void loop() {

  // if we lost connection, we attempt to reconnect (blocking)
  if (!is_client_conected()) { 

    Serial.println("Client not connected!");
    
    connect_client("192.168.4.2"); 
    sendJSON("type", "esp32");
  }

  poll();

  gripType = getGT();

  if (gripType != lastGripType) {
    lastGripType = gripType;
    for (int i = 0; i < gripType; i ++) { //pulso de salida frecuencia de 1s
      digitalWrite(GT_PIN, HIGH);
      delay(500);
      digitalWrite(GT_PIN, LOW);
      delay(500);
    }
  }

  EMGA = digitalRead(EMGA_PIN); 
  EMGB = digitalRead(EMGB_PIN);

  if (EMGA != lastEMGA && EMGA == LOW) {
    lastEMGA = EMGA;
    EMGA_counter++;
    sendJSON("EMGA_counter", String(EMGA_counter).c_str());
  }

  if (EMGB != lastEMGB && EMGB == LOW) {
    lastEMGB = EMGB;
    EMGB_counter++;
    sendJSON("EMGB_counter", String(EMGB_counter).c_str());
  }

  lastEMGA = EMGA;
  lastEMGB = EMGB;
}