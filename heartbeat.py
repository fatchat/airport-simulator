import time
import paho.mqtt.client as mqtt
import argparse

MQTT_BROKER = "localhost"

parser = argparse.ArgumentParser(description="Heartbeat Publisher")
parser.add_argument("interval", type=int, help="Heartbeat interval in seconds")
args = parser.parse_args()


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER)
    while True:
        client.publish("heartbeat")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
