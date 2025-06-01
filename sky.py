"""Airport Simulation using MQTT"""

import json
import random
import threading
import argparse
from redis import Redis
from flask import Flask, jsonify
import paho.mqtt.client as mqtt
from plane import Plane

MQTT_BROKER = "localhost"
HEARTBEAT_INTERVAL = 1  # seconds

redis_client = Redis(host="localhost", port=6379)


class Sky:
    def __init__(self):
        self.plane_queue = []
        self.next_plane_id = 0

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Sky")
        self.client.connect(MQTT_BROKER)
        self.client.subscribe("heartbeat")
        self.client.subscribe("send_next_plane")
        self.client.message_callback_add("heartbeat", self.on_heartbeat)
        self.client.message_callback_add("send_next_plane", self.send_next_plane)
        self.client.publish("logs", "[Sky] Sky initialized, waiting for planes...")

    def to_dict(self):
        """Convert the Sky instance to a JSON representation."""
        return {
            "plane_queue": [plane.to_dict() for plane in self.plane_queue],
            "next_plane_id": self.next_plane_id,
        }

    @staticmethod
    def from_dict(data):
        """Load the Sky state from a JSON representation."""
        restored_sky = Sky()
        restored_sky.plane_queue = [
            Plane.from_dict(plane_data) for plane_data in data.get("plane_queue", [])
        ]
        restored_sky.next_plane_id = data.get("next_plane_id", 0)
        return restored_sky

    def add_new_plane(self):
        """Add a new plane to the queue."""
        plane_id = f"plane_{self.next_plane_id}"
        with state_lock:
            self.next_plane_id += 1
            plane = Plane(plane_id)
            self.plane_queue.append(plane)
        self.client.publish(
            "logs",
            f"[Sky] New plane added: {plane.plane_id} -> gate {plane.destination_gate}",
        )

    def send_next_plane(self, client, userdata, msg):  # pylint:disable=unused-argument
        """runway requests next plane"""
        with state_lock:
            if self.plane_queue:
                message = json.loads(msg.payload.decode())
                if "gate_number" in message:
                    plane: Plane = self.plane_queue.pop(0)
                    plane.state = "on_runway"
                    plane.destination_gate = message["gate_number"]
                    self.client.publish("runway", json.dumps(plane.to_dict()))
                    self.client.publish(
                        "logs",
                        f"[Sky] Sent plane {plane.plane_id} to runway; destination gate {plane.destination_gate}",
                    )

    def on_heartbeat(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle heartbeat messages to add new planes."""
        redis_client.set("sky", json.dumps(self.to_dict()))
        if random.random() < 0.3:
            self.add_new_plane()
        else:
            self.client.publish("logs", "[Sky] No new plane added this tick")


parser = argparse.ArgumentParser(description="Gate Simulation")
parser.add_argument("--http-port", type=int, default=5000, help="HTTP server port")
args = parser.parse_args()

saved_state = redis_client.get("sky")
if saved_state:
    print("Restoring saved state from Redis...")
    saved_state = json.loads(saved_state.decode())
    sky = Sky.from_dict(saved_state)
else:
    sky = Sky()

state_lock = threading.Lock()
app = Flask("Sky")


@app.route("/state")
def get_state():
    """HTTP endpoint to get the current state of the sky."""
    with state_lock:
        return jsonify(sky.to_dict())


def start_http_server():
    """Start the HTTP server to serve sky state."""
    app.run(host="0.0.0.0", port=args.http_port, threaded=True)


def start_mqtt_client():
    """Start the MQTT client to handle sky operations."""
    sky.client.loop_forever()


if __name__ == "__main__":
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.start()

    http_thread = threading.Thread(target=start_http_server)
    http_thread.start()
