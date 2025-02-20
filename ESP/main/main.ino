#include "config.h"
#include "wifi_communicator.h"
#include <esp_wifi.h>
#include <esp_netif.h>
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_log.h"
#include <ESPping.h>
#include <ArduinoJson.h>
#include <ArduinoWebsockets.h>


//button values
int buttonState = 0;
int buttonLastState = 0;
int gripType = 0;

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
  
  pinMode(BTN_PIN, INPUT_PULLUP); //Simulador EMG
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

  for (int i = 0; i < gripType; i ++) { //pulso de salida frecuencia de 1s
    digitalWrite(GT_PIN, HIGH);
    delay(500);
    digitalWrite(GT_PIN, LOW);
    delay(500);
  }

  buttonState = digitalRead(BTN_PIN); 

  if (buttonState != buttonLastState) { //Detección de borda
    if (buttonState == 1) {
      sendJSON("EMG_counter", "2");
    }
  }

  buttonLastState = buttonState;
}