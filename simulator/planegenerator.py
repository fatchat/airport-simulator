"""Program which continuously generates flights"""

import time
import json
from random import random, randint
import os
import argparse
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")


class PlaneGenerator:
    """Generator class"""

    def __init__(self, prob: float, airports: list[str]):
        """constructor"""
        self.prob = prob
        self.airports = airports

        self.ready = False
        self.connect_failed = False

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "PlaneGenerator")
        self.client.on_connect = self.on_connect
        self.client.on_connect_fail = self.on_connect_fail
        self.client.connect(MQTT_BROKER)
        self.client.loop_start()

    def on_connect(
        self, mqtt_client: mqtt.Client, userdata, connect_flags, reason_code, properties
    ):
        """called by broker upon connection"""
        print("connected!")
        self.client.subscribe("admin")
        self.client.message_callback_add("admin", self.on_admin)
        self.ready = True

    def on_connect_fail(self, mqtt_client: mqtt.Client, userdata):
        """if connection to the mqtt broker fails"""
        self.connect_failed = True

    def on_admin(
        self,
        mqtt_client,  # pylint:disable=unused-argument
        userdata,  # pylint:disable=unused-argument
        msg: mqtt.MQTTMessage,
    ):
        """Handler for mqtt_topic"""
        payload = msg.payload.decode()
        try:
            message = json.loads(payload)
        except json.decoder.JSONDecodeError:
            return
        if message["command"] == "quit":
            self.client.disconnect()

    def attempt_to_generate_flight(self):
        """generate flight probabalistically"""
        if random() < self.prob:
            self.generate_flight()

    def generate_flight(self):
        """choose two airports at random and queue a flight between them"""
        from_idx = randint(0, len(self.airports) - 1)
        to_idx = randint(0, len(self.airports) - 1)
        while to_idx == from_idx:
            to_idx = randint(0, len(self.airports) - 1)

        from_airport = self.airports[from_idx]
        to_airport = self.airports[to_idx]

        topic = f"airport/{from_airport}"
        message = {"msg_type": "new_plane", "end_airport": to_airport}

        self.client.publish(topic, json.dumps(message))
        print(f"Created flight from {from_airport} to {to_airport}")


def main():
    """main"""
    parser = argparse.ArgumentParser(description="Flight generator")
    parser.add_argument("--interval", type=float, help="Attempt frequency in seconds")
    parser.add_argument("--prob", type=float, help="Probability of generating a flight")
    parser.add_argument(
        "--interactive", action="store_true", help="Press <Enter> to advance time"
    )
    parser.add_argument("airports", nargs="+")
    args = parser.parse_args()

    airports = list(set(args.airports))
    if len(airports) < 2:
        print("We need at least two distinct airports")
        return

    print(f"Flight generation probability is {args.prob}")
    print("Airports are " + ",".join(airports))

    plane_generator = PlaneGenerator(args.prob, airports)

    while not plane_generator.ready:
        if plane_generator.connect_failed:
            print("could not connect to mqtt broker")
            return
        print("waiting to connect to broker...")
        time.sleep(1)

    while True:
        plane_generator.attempt_to_generate_flight()
        if args.interactive:
            input()
        else:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
