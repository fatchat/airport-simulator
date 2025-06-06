"""Runway module for handling plane arrivals and sending them to gates."""

import random
import json
import argparse
from redis import Redis
import paho.mqtt.client as mqtt
from plane import Plane
from logger import Logger

MQTT_BROKER = "localhost"
REDIS_BROKER = "localhost"

redis_client = Redis(host=REDIS_BROKER, port=6379)


class Runway:
    def __init__(self, **kwargs):
        """Runway listens for planes arriving and sends them to gates after 3 ticks."""
        self.current_plane = None
        self.free_gates = set()

        self.RUNWAY_MIN_TICKS = 3  # Minimum ticks a plane stays on the runway
        self.RUNWAY_MAX_TICKS = 10

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Runway")
        self.client.connect(MQTT_BROKER)

        self.client.subscribe("runway")
        self.client.message_callback_add("runway", self.on_plane_arrival)

        self.client.subscribe("heartbeat")
        self.client.message_callback_add("heartbeat", self.on_heartbeat)

        self.client.subscribe("gate_updates")
        self.client.message_callback_add("gate_updates", self.on_gate_update)

        self.logger = Logger(
            "Runway", self.client, verbose=kwargs.get("verbose", False)
        )
        self.logger.log("Runway initialized, waiting for planes...")

    def to_dict(self):
        """Convert the Runway instance to a JSON representation."""
        return {
            "current_plane": (
                self.current_plane.to_dict() if self.current_plane else None
            ),
            "free_gates": list(self.free_gates),
        }

    @staticmethod
    def from_json(data, **kwargs):
        """Load the Runway state from a JSON representation."""
        restored_runway = Runway(**kwargs)
        if data.get("current_plane"):
            restored_runway.current_plane = Plane.from_dict(data["current_plane"])
        restored_runway.free_gates = set(data.get("free_gates", []))
        return restored_runway

    def on_plane_arrival(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle plane arrivals on the runway."""
        plane = json.loads(msg.payload.decode())
        if not self.current_plane:
            self.current_plane = Plane.from_dict(plane)
            self.current_plane.ticks_on_runway = random.randint(
                self.RUNWAY_MIN_TICKS, self.RUNWAY_MAX_TICKS
            )
            self.logger.log(f"Plane {plane['plane_id']} arrived on runway")
        else:
            self.logger.log(
                f"ERROR!!! Plane {plane['plane_id']} arrived but runway "
                + f"is occupied by {self.current_plane['plane_id']}",
            )

    def advance_plane(self):
        """Advance the plane on the runway, check if it can be sent to a gate."""
        self.current_plane.ticks_on_runway -= 1
        if self.current_plane.ticks_on_runway <= 0:
            topic = f"gate/{self.current_plane.destination_gate}"
            self.client.publish(topic, json.dumps(self.current_plane.to_dict()))
            self.logger.log(
                f"Sent plane {self.current_plane.plane_id} to gate "
                + f"{self.current_plane.destination_gate}",
            )
            self.current_plane = None
        else:
            self.logger.log(
                f"Plane {self.current_plane.plane_id} still on runway, "
                + f"ticks: {self.current_plane.ticks_on_runway}",
            )

    def on_gate_update(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle updates from gates, reset current plane if gate is free."""
        gate_update = json.loads(msg.payload.decode())
        gate_number = gate_update.get("gate_number")
        if gate_number and gate_update.get("state") == "free":
            self.logger.log(f"Gate {gate_number} is now free.")
            self.free_gates.add(gate_number)
        if gate_number and gate_update.get("state") == "closed":
            if gate_number in self.free_gates:
                self.logger.log(f"Gate {gate_number} is now closed.")
                self.free_gates.remove(gate_number)

    def on_heartbeat(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle heartbeat messages to advance the runway state."""
        redis_client.set("runway", json.dumps(self.to_dict()))
        if self.current_plane:
            self.advance_plane()

        if self.current_plane is None and len(self.free_gates) > 0:
            gate_number = self.free_gates.pop()
            self.client.publish(
                "send_next_plane", json.dumps({"gate_number": gate_number})
            )
            self.logger.log("Ready for next plane")


parser = argparse.ArgumentParser(description="Gate Simulation")
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()

saved_state = redis_client.get("runway")
if saved_state:
    print("Restoring saved state from Redis...")
    saved_state = json.loads(saved_state.decode())
    runway = Runway.from_json(saved_state, verbose=args.verbose)
else:
    runway = Runway(verbose=args.verbose)


runway.client.loop_forever()
