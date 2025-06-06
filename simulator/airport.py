"""Airport Simulation using MQTT"""

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


def comma_separated_list(value):
    """Convert a comma-separated string into a list for argparse."""
    return value.split(",")


def redis_key(airport_name: str) -> str:
    """Generate the Redis key for the airport."""
    return f"airport-{airport_name}"


class Airport:
    """Representation of an airport"""

    def __init__(self, airport: str, runways: list, gates: list, **kwargs):
        """Initialize the airport with a name and empty gates."""
        self.airport = airport
        self.runways = runways if runways else []
        self.gates = gates if gates else []

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, f"Airport_{airport}"
        )
        self.client.connect(MQTT_BROKER)

        topic = f"airport/{airport}"
        self.client.subscribe(topic)

        self.client.subscribe("heartbeat")
        self.client.message_callback_add("heartbeat", self.on_heartbeat)

        self.logger = Logger(self.client, verbose=kwargs.get("verbose", False))

        self.logger.log(f"[Airport {self.airport}] Initialized")
        self.logger.log(f"[Airport {self.airport}] Runways: {self.runways}")
        self.logger.log(f"[Airport {self.airport}] Gates: {self.gates}")
        self.logger.log(f"[Airport {self.airport}] Waiting for planes...")

    def to_dict(self):
        """Convert the Airport instance to a dict representation."""
        return {
            "airport": self.airport,
            "runways": self.runways,
            "gates": self.gates,
        }

    @staticmethod
    def from_dict(data: dict, **kwargs):
        """Load the Airport state from a dict representation."""
        restored_airport = Airport(
            data["airport"], data["runways"], data["gates"], **kwargs
        )
        return restored_airport

    def on_heartbeat(self, client, userdata, msg):  # pylint:disable=unused-argument
        """Handle heartbeat messages to update gate state."""
        redis_client.set(redis_key(self.airport), json.dumps(self.to_dict()))
        self.logger.log(f"[Airport {self.airport}] Heartbeat received, state updated.")


# == main
parser = argparse.ArgumentParser(description="Airport Simulation")
parser.add_argument("--airport", required=True, type=str, help="The airport name")
parser.add_argument(
    "--runways",
    required=True,
    type=comma_separated_list,
    help="The runway names",
)
parser.add_argument(
    "--gates",
    required=True,
    type=comma_separated_list,
    help="The gate names",
)
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()

saved_state = redis_client.get(redis_key(args.airport))
if saved_state:
    print("Restoring saved state from Redis...")
    saved_state = json.loads(saved_state.decode())
    the_airport = Airport.from_dict(saved_state, verbose=args.verbose)
else:
    the_airport = Airport(args.airport, args.runways, args.gates, verbose=args.verbose)

the_airport.client.loop_forever()
