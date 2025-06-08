import time
import json
import argparse
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"

parser = argparse.ArgumentParser(description="Heartbeat Publisher")
parser.add_argument("interval", type=float, help="Heartbeat interval in seconds")
args = parser.parse_args()


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER)
    ticks = 0
    while True:
        ticks += 1
        client.publish("heartbeat", json.dumps({"ticks": ticks}))
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
