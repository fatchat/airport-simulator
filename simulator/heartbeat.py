import time
import json
import os
import argparse
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")

parser = argparse.ArgumentParser(description="Heartbeat Publisher")
parser.add_argument("interval", type=float, help="Heartbeat interval in seconds")
parser.add_argument(
    "--interactive", action="store_true", help="Press <Enter> to advance time"
)
parser.add_argument("--start-tick", help="tick to start at", default=0, type=int)
args = parser.parse_args()


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER)
    ticks = args.start_tick
    while True:
        ticks += 1
        client.publish("heartbeat", json.dumps({"ticks": ticks}))
        if args.interactive:
            input()
        else:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
