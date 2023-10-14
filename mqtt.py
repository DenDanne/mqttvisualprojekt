import os
import sys
import logging
import paho.mqtt.client as mqtt
import json
import csv
import random
import base64
import binascii
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta

USER = "lora-test-ful@ttn"
PASSWORD = "NNSXS.43M3AY73ECK6MFPXQ3X5THOV27SAY224UJXBUOQ.4JO563N3PQHPHLHOYYBYCVHMNFCYXNPNPAOTSLUNVMPNKND763RA"
PUBLIC_TLS_ADDRESS = "eu1.cloud.thethings.network"
PUBLIC_TLS_ADDRESS_PORT = 8883
DEVICE_ID = "eui-2cf7f12032304b2d"
ALL_DEVICES = True

# Meaning Quality of Service (QoS)
# QoS = 0 - at most once
# The client publishes the message, and there is no acknowledgement by the broker.
# QoS = 1 - at least once
# The broker sends an acknowledgement back to the client.
# The client will re-send until it gets the broker's acknowledgement.
# QoS = 2 - exactly once
# Both sender and receiver are sure that the message was sent exactly once, using a kind of handshake
QOS = 0

DEBUG = True

def decode_payload(encoded_payload):
    try:
        decoded_bytes = base64.b64decode(encoded_payload)
        decoded_str = decoded_bytes.decode('ascii')
        return decoded_str
    except binascii.Error as e:
        print(f"Failed to decode base64: {e}")
    except UnicodeDecodeError as e:
        print(f"Decoded bytes are not a valid ASCII string: {e}")
    return None

def get_value_from_json_object(obj, key):
    try:
        return obj[key]
    except KeyError:
        return '-'


def stop(client):
    client.disconnect()
    print("\nExit")
    sys.exit(0)

def save_to_file(some_json):
    end_device_ids = some_json["end_device_ids"]
    device_id = end_device_ids["device_id"]
    application_id = end_device_ids["application_ids"]["application_id"]
    received_at_full = some_json["received_at"]

    if 'uplink_message' in some_json:
        uplink_message = some_json["uplink_message"]
        f_port = get_value_from_json_object(uplink_message, "f_port")

        # check if f_port is found
        if f_port != '-':
            # Extract desired parts of received_at
            received_at = received_at_full.split("T")[1].split(":")[0] + ":" + received_at_full.split("T")[1].split(":")[1]
            
            # Decode frm_payload from base64 to ASCII
            frm_payload_encoded = uplink_message["frm_payload"]
            frm_payload = decode_payload(frm_payload_encoded)
            
            # File to write to
            path_n_file = "resultat.txt"
            print(path_n_file)
            
            last_time = None
            data_to_write = f"{received_at} {frm_payload}\n"
            
            # Check if file exists and is not empty
            if os.path.exists(path_n_file) and os.path.getsize(path_n_file) > 0:
                # Read last line of file
                with open(path_n_file, 'r') as txtFile:
                    lines = txtFile.readlines()
                    last_line = lines[-1]
                    last_time = last_line.split()[0]  # Assuming time is always available
            
            # Check if last time is the same as current time
            if last_time == received_at:
                # Append data to last line
                data_to_write = lines[-1].strip() + frm_payload + "\n"
                lines[-1] = data_to_write  # Replace last line
                # Write back all lines
                with open(path_n_file, 'w', newline='') as txtFile:
                    txtFile.writelines(lines)
            else:
                # Add new line with new time
                with open(path_n_file, 'a', newline='') as txtFile:
                    txtFile.write(data_to_write)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("\nConnected successfully to MQTT broker")
    else:
        print("\nFailed to connect, return code = " + str(rc))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, message):
    print("\nMessage received on topic '" + message.topic + "' with QoS = " + str(message.qos))

    parsed_json = json.loads(message.payload)

    if DEBUG:
        print("Payload (Collapsed): " + str(message.payload))
        print("Payload (Expanded): \n" + json.dumps(parsed_json, indent=4))

    save_to_file(parsed_json)


# mid = message ID
# It is an integer that is a unique message identifier assigned by the client.
# If you use QoS levels 1 or 2 then the client loop will use the mid to identify messages that have not been sent.
def on_subscribe(client, userdata, mid, granted_qos):
    print("\nSubscribed with message id (mid) = " + str(mid) + " and QoS = " + str(granted_qos))


def on_disconnect(client, userdata, rc):
    print("\nDisconnected with result code = " + str(rc))


def on_log(client, userdata, level, buf):
    print("\nLog: " + buf)
    logging_level = client.LOGGING_LEVEL[level]
    logging.log(logging_level, buf)


# Generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'

print("Create new mqtt client instance")
mqttc = mqtt.Client(client_id)

print("Assign callback functions")
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message
mqttc.on_disconnect = on_disconnect
# mqttc.on_log = on_log  # Logging for debugging OK, waste

# Setup authentication from settings above
mqttc.username_pw_set(USER, PASSWORD)

# IMPORTANT - this enables the encryption of messages
mqttc.tls_set()  # default certification authority of the system

# mqttc.tls_set(ca_certs="mqtt-ca.pem") # Use this if you get security errors
# It loads the TTI security certificate. Download it from their website from this page: 
# https://www.thethingsnetwork.org/docs/applications/mqtt/api/index.html
# This is normally required if you are running the script on Windows

print("Connecting to broker: " + PUBLIC_TLS_ADDRESS + ":" + str(PUBLIC_TLS_ADDRESS_PORT))
mqttc.connect(PUBLIC_TLS_ADDRESS, PUBLIC_TLS_ADDRESS_PORT, 60)


if ALL_DEVICES:
    print("Subscribe to all topics (#) with QoS = " + str(QOS))
    mqttc.subscribe("#", QOS)
elif len(DEVICE_ID) != 0:
    topic = "v3/" + USER + "/devices/" + DEVICE_ID + "/up"
    print("Subscribe to topic " + topic + " with QoS = " + str(QOS))
    mqttc.subscribe(topic, QOS)
else:
    print("Can not subscribe to any topic")
    stop(mqttc)


print("And run forever")
try:
    run = True
    while run:
        mqttc.loop(10)  # seconds timeout / blocking time
        print(".", end="", flush=True)  # feedback to the user that something is actually happening
except KeyboardInterrupt:
    stop(mqttc)