import ssl
import time
from datetime import datetime, timedelta
from os import environ
from sys import exit

import paho.mqtt.client as mqtt
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from dotenv import load_dotenv

load_dotenv()

androbd_topic = environ.get("ANDROBD_TOPIC", None)
seconds_before_down = int(environ.get("ANDROBD_INACTIVE_THRESHOLD", "60"))
mqtt_host = environ.get("MQTT_HOST", None)
mqtt_port = environ.get("MQTT_PORT", None)
mqtt_client_id = environ.get("MQTT_CLIENT_ID", "androbd-exporter")
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

required = [androbd_topic, mqtt_host, mqtt_port]
if None in required:
    raise "Required options not passed in env"

state = {
    "running_time": 0,
    "running_time_last_updated": datetime.now(),
    "last_data": {},
    "is_up": True,
    "seconds_before_down": seconds_before_down,
    "timedelta_before_down": timedelta(seconds=seconds_before_down)
}

# running_time = 0
# # This can't be a plain variable but it has to be a dict so the reference is preserved between the
# # exporter and mqtt
# running_time_last_updated = {
#     "time": datetime.now()
# }

# last_data = {}
# is_up = True
# seconds_before_down = 1 * 60 # 5 mins
# td = timedelta(seconds=seconds_before_down)

def on_running_time_update(client, userdata, msg):
    running_time = msg.payload.decode("utf-8")
    state["running_time_last_updated"] = datetime.now()
    print("Running_time updated!", state["running_time_last_updated"])


class AndroOBDCollector(object):
    def collect(self):
        now = datetime.now()
        diff = now - state["running_time_last_updated"]
        state["is_up"] = diff < state["timedelta_before_down"]
        print(diff, state["running_time_last_updated"], state["is_up"])
        yield GaugeMetricFamily('androbd_up', "If androbd is submitting data", value=1 if state["is_up"] else 0)
        
        if not state["is_up"]:
            return
        
        for key in state["last_data"]:
            yield GaugeMetricFamily(f"androbd_{key}", f'androbd data: {key}', value=state["last_data"][key])


def on_connect(client, userdata, flags, rc):  # The callback for when 
    # the client connects to the broker 
    print("Connected with result code {0}".format(str(rc)))  

    client.subscribe(f"{androbd_topic}/#")
    client.message_callback_add(f"{androbd_topic}/running_time", on_running_time_update)



def on_message(client, userdata, msg):  
    print("Message received-> " + msg.topic + " " + str(msg.payload))  # Print a received msg
    split_topic = msg.topic.split("/")
    sensor = split_topic[-1]
    state["last_data"][sensor] = msg.payload.decode("utf-8")
    # print(split_topic, sensor, state["last_data"][sensor])

def on_disconnect(client, userdata, rc):
    if rc == 7:
        print("There's a conflicting client-id listening, Please change the client id!")
        exit()
    if rc != 0:
        print("Unexpected disconnection." + str(rc))


if __name__ == '__main__':
    REGISTRY.register(AndroOBDCollector())
    start_http_server(3000)

    client = mqtt.Client(mqtt_client_id, transport = "websockets" if mqtt_is_ws else "tcp")  # Create instance of client
    client.on_connect = on_connect  # Define callback function for successful connection
    client.on_message = on_message  # Define callback function for receipt of a message
    client.on_disconnect = on_disconnect
    
    if mqtt_is_ws:
        client.ws_set_options(path=mqtt_ws_path)

    if mqtt_is_tls:
        client.tls_set(mqtt_tls_ca_cert, mqtt_tls_certfile, mqtt_tls_keyfile, ssl.CERT_NONE if mqtt_tls_ignore_invalid_certs else ssl.CERT_REQUIRED)
        if mqtt_tls_ignore_invalid_certs:
            client.tls_insecure_set(true)

    client.username_pw_set(mqtt_username, mqtt_password)

    client.connect(mqtt_host, int(mqtt_port))
    client.loop_forever()  # Start networking daemon
    
    # while True:
    #     time.sleep(30)
