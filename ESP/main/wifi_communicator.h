#ifndef __WIFI_COMMUNICATOR_H__
#define __WIFI_COMMUNICATOR_H__

#include "my_wifi.h"
#include "config.h"
#include <ArduinoJson.h>
#include <ArduinoWebsockets.h>

static SemaphoreHandle_t _send_tsk_mutex;
static SemaphoreHandle_t _recv_tsk_mutex;

static QueueHandle_t _send_q;
static QueueHandle_t _recv_q;
static TaskHandle_t _socket_reporter_task_h = NULL;

// The sockets client
using namespace websockets;

WebsocketsClient client;

int GT = 0;
/*
  Attempt to connect the client
*/

int getGT() {
  return GT;
}

void onMessageCallback(WebsocketsMessage message) {
  Serial.print("Mensagem recebida do servidor: ");
  Serial.println(message.data());

  // Converte a mensagem recebida em JSON
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message.data());

  if (error) {
    Serial.println("Erro ao interpretar JSON recebido!");
    return;
  }

  // Processa os dados recebidos
  if (doc.containsKey("GT")) {
    GT = doc["GT"];
  }
}

void connect_client(String serverAdress){
  // We have to connect, no other options
  while(!client.connect(serverAdress, SERVER_PORT, "/")){ 
  Serial.println("Client not connected!");delay(1000); }
  client.onMessage(onMessageCallback);
  Serial.println("Client Connected!!!");
}

bool is_client_conected(){
  return client.available();
}

void sendJSON(const char *key, const char *value) {
  // Cria um documento JSON
  StaticJsonDocument<256> doc;
  doc[key] = value;  

  // Serializa o JSON para string
  String jsonString;
  serializeJson(doc, jsonString);

  // Envia o JSON via WebSocket
  client.send(jsonString);
}

void poll(){ client.poll();}

#endif // __WIFI_COMMUNICATOR_H__
