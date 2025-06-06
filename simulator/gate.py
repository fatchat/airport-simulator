"""Airport Simulation using MQTT"""

import random
import json
import threading
import argparse
from redis import Redis
import paho.mqtt.client as mqtt
from plane import Plane

MQTT_BROKER = "localhost"
REDIS_BROKER = "localhost"

redis_client = Redis(host=REDIS_BROKER, port=6379)


class Gate:
    def __init__(self, gate_number: str):
        self.gate_number = gate_number
        self.current_plane = None

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, f"Gate_{gate_number}"
        )
        self.client.connect(MQTT_BROKER)

        topic = f"gate/{gate_number}"
        self.client.subscribe(topic)
        self.client.message_callback_add(topic, self.receive_plane)

        self.client.on_disconnect = lambda client, userdata, rc: client.publish(
            "runway", json.dumps({"state": "closed", "gate_number": gate_number})
        )

        self.client.subscribe("heartbeat")
        self.client.message_callback_add("heartbeat", self.on_heartbeat)

        self.client.publish(
            "logs", f"[Gate {self.gate_number}] Initialized, waiting for planes..."
        )

    def to_dict(self):
        """Convert the Gate instance to a dict representation."""
        return {
            "gate_number": self.gate_number,
            "current_plane": (
                self.current_plane.to_dict() if self.current_plane else None
            ),
        }

    @staticmethod
    def from_dict(data):
        """Load the Gate state from a dict representation."""
        restored_gate = Gate(data["gate_number"])
        if data.get("current_plane"):
            restored_gate.current_plane = Plane.from_dict(data["current_plane"])
        return restored_gate

    def receive_plane(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle incoming plane messages at the gate."""
        self.current_plane = Plane.from_dict(json.loads(msg.payload.decode()))
        self.current_plane.state = "at_gate"
        self.current_plane.time_at_gate = random.randint(
            3, 5
        )  # Random time at gate between 3 and 5 ticks
        self.client.publish(
            "logs",
            f"[Gate {self.gate_number}] Plane {self.current_plane.plane_id} has arrived; "
            + f"time at gate: {self.current_plane.time_at_gate} ticks",
        )

    def on_heartbeat(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle heartbeat messages to update gate state."""
        redis_client.set(f"gate-{self.gate_number}", json.dumps(self.to_dict()))
        if self.current_plane:
            self.client.publish(
                "logs",
                f"[Gate {self.gate_number}] Holding plane {self.current_plane.plane_id} "
                + f"for {self.current_plane.time_at_gate} ticks.",
            )
            self.current_plane.time_at_gate -= 1
            if self.current_plane.time_at_gate <= 0:
                self.client.publish(
                    "logs",
                    f"[Gate {self.gate_number}] Plane {self.current_plane.plane_id} "
                    + "has left the gate.",
                )
                self.current_plane = None
                self.client.publish(
                    "gate_updates",
                    json.dumps({"gate_number": self.gate_number, "state": "free"}),
                )
        if self.current_plane is None:
            self.client.publish(
                "gate_updates",
                json.dumps({"gate_number": self.gate_number, "state": "free"}),
            )
            self.client.publish("logs", f"[Gate {self.gate_number}] No plane at gate.")


# == main
parser = argparse.ArgumentParser(description="Gate Simulation")
parser.add_argument(
    "gate_number",
    type=str,
    help="The gate number to simulate (e.g., '1', '2', etc.)",
)
args = parser.parse_args()

saved_state = redis_client.get(f"gate-{args.gate_number}")
if saved_state:
    print("Restoring saved state from Redis...")
    saved_state = json.loads(saved_state.decode())
    gate = Gate.from_dict(saved_state)
else:
    gate = Gate(args.gate_number)

gate.client.loop_forever()
