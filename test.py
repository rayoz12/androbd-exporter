import ssl
import time
from datetime import datetime, timedelta
from os import environ
from sys import exit

import paho.mqtt.client as mqtt

from dotenv import load_dotenv
load_dotenv()

androbd_topic = environ.get("ANDROBD_TOPIC", None)
mqtt_host = environ.get("MQTT_HOST", None)
mqtt_port = environ.get("MQTT_PORT", None)
mqtt_is_ws = "MQTT_WS_ON" in environ
mqtt_ws_path = environ.get("MQTT_WS_PATH", "/mqtt")
mqtt_is_tls = "MQTT_TLS_ON" in environ
mqtt_tls_ca_cert = environ.get("MQTT_TLS_CA_CERT", None)
mqtt_tls_certfile = environ.get("MQTT_TLS_CERTFILE", None)
mqtt_tls_keyfile = environ.get("MQTT_TLS_KEYFILE", None)
# see https://docs.python.org/3/library/ssl.html#ssl.CERT_NONE. Defaults to "FALSE", can be set to "TRUE"
mqtt_tls_ignore_invalid_certs = environ.get("MQTT_IGNORE_INVALID_CERTS", "FALSE")
mqtt_tls_ignore_invalid_certs = mqtt_tls_ignore_invalid_certs == "TRUE"

mqtt_username = environ.get("MQTT_USERNAME", None)
mqtt_password = environ.get("MQTT_PASSWORD", None)

start_time = time.time()

def on_connect(client, userdata, flags, rc):  # The callback for when 
    # the client connects to the broker 
    print("Connected with result code {0}".format(str(rc)))  

def on_disconnect(client, userdata, rc):
    if rc == 7:
        print("There's a conflicting client-id listening, Please change the client id!")
        exit()
    if rc != 0:
        print("Unexpected disconnection." + str(rc))

client = mqtt.Client("androbd-exporter-test", transport = "websockets" if mqtt_is_ws else "tcp")  # Create instance of client
client.on_connect = on_connect  # Define callback function for successful connection
client.on_disconnect = on_disconnect

if mqtt_is_ws:
    client.ws_set_options(path=mqtt_ws_path)

if mqtt_is_tls:
    client.tls_set(mqtt_tls_ca_cert, mqtt_tls_certfile, mqtt_tls_keyfile, ssl.CERT_NONE if mqtt_tls_ignore_invalid_certs else ssl.CERT_REQUIRED)
    if mqtt_tls_ignore_invalid_certs:
        client.tls_insecure_set(true)

client.username_pw_set(mqtt_username, mqtt_password)

client.connect(mqtt_host, int(mqtt_port))
# client.loop_forever()  # Start networking daemon

while True:
    time.sleep(2)
    elapsedSeconds = time.time() - start_time
    elapsedHours = elapsedSeconds / 3600
    print(elapsedSeconds, elapsedHours)
    client.publish(f"{androbd_topic}/running_time", elapsedHours)