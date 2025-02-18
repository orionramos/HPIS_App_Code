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

// Communication messages
char incoming_msg[MAX_BUFFER_LEN] = { 0 };
char response[MAX_BUFFER_LEN] = { 0 };

//button values
int buttonState = 0;
int buttonLastState = 0;
int gripType = 0;
String serverIPAdress = "";

const char* websocket_server = SERVER_ADDRESS;
const uint16_t websocket_port = SERVER_PORT;

static const char *TAG = "findServerIP";

/*String findServerIP() {
    const uint8_t serverMac[6] = {0xA4, 0xF9, 0x33, 0x10, 0x58, 0xEC}; // Replace with the server's MAC address

    wifi_sta_list_t wifi_sta_list;
    esp_netif_sta_list_t netif_sta_list;

    // Get the list of connected stations
    if (esp_wifi_ap_get_sta_list(&wifi_sta_list) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to get the list of connected devices.");
        return "";
    }

    // Initialize the netif_sta_list
    memset(&netif_sta_list, 0, sizeof(netif_sta_list));
    netif_sta_list.num = wifi_sta_list.num;
    netif_sta_list.sta = (esp_netif_sta_info_t*)malloc(sizeof(esp_netif_sta_info_t) * wifi_sta_list.num);

    if (!netif_sta_list.sta) {
        ESP_LOGE(TAG, "Memory allocation failed.");
        return "";
    }

    // Get the list of IP addresses
    if (esp_netif_get_sta_list(&wifi_sta_list, &netif_sta_list) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to get the list of IP addresses.");
        free(netif_sta_list.sta);
        return "";
    }

    // Iterate through the list of connected devices
    for (int i = 0; i < wifi_sta_list.num; i++) {
        esp_netif_sta_info_t station = netif_sta_list.sta[i];

        // Compare MAC addresses
        if (memcmp(station.mac, serverMac, 6) == 0) {
            char ipStr[16];
            snprintf(ipStr, sizeof(ipStr), "%d.%d.%d.%d",
                     (station.ip.addr >> 0) & 0xFF,
                     (station.ip.addr >> 8) & 0xFF,
                     (station.ip.addr >> 16) & 0xFF,
                     (station.ip.addr >> 24) & 0xFF);
            ESP_LOGI(TAG, "Server IP: %s", ipStr);
            free(netif_sta_list.sta);
            return ipStr;
        }
    }

    free(netif_sta_list.sta);
    ESP_LOGI(TAG, "Server not found.");
    return ";"
}*/

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.mode(WIFI_AP);  //Optional
  WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("\nWiFi network established!");
  Serial.println(WiFi.softAPIP());

  //serverIPAdress = findServerIP();
  IPAddress ip (192, 168, 4, 2); // The remote ip to ping
  
  while (!Ping.ping(ip)) {
    //serverIPAdress = findServerIP();
    Serial.println("!PING");
    delay(1000);
  }

  Serial.println("PING!");

  //setup_wifi_communicator();

  Serial.println(is_client_conected());

  pinMode(LED_PIN, OUTPUT);
  
  pinMode(BTN_PIN, INPUT_PULLUP);
}

void loop() {

  // if we lost connection, we attempt to reconnect (blocking)
  if (!is_client_conected()) { 

    Serial.println("Client not connected!");

    /*serverIPAdress = findServerIP();
    while (serverIPAdress == "") {
      serverIPAdress = findServerIP();
    }*/
    
    connect_client("192.168.4.2"); 
    sendJSON("type", "esp32");
  }

  poll();

  gripType = getGT();

  Serial.print("Valor recebido: ");
  Serial.println(gripType);

  for (int i = 0; i < gripType; i ++) {
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
    delay(500);
  }

  buttonState = digitalRead(BTN_PIN); 

  if (buttonState != buttonLastState) {
    if (buttonState == 1) {
      sendJSON("EMG_counter", "2");
    }
  }

  buttonLastState = buttonState;
}