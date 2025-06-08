"""Airport Simulation using MQTT"""

import random
import json
from enum import Enum
import argparse
from redis import Redis

from restorable import construct_or_restore
from airportcomponent import AirportComponent
from plane import Plane, PlaneState

REDIS_BROKER = "localhost"


class GateState(Enum):
    """Enumeration for gate states."""

    FREE = "free"
    IN_USE_DEPARTING = "in-use-departing"
    IN_USE_ARRIVING = "in-use-arriving"
    CLOSED = "closed"


def gate_redis_key(airport: str, gate_number: str) -> str:
    """Generate the Redis key for a specific gate."""
    return f"airport-{airport}-gate-{gate_number}"


class Gate(AirportComponent):
    """Representation of a gate at an airport."""

    @staticmethod
    def args_to_dict(arguments: argparse.Namespace) -> dict:
        """Convert command line arguments to a state dictionary."""
        return {
            "airport": arguments.airport,
            "gate_number": arguments.gate_number,
        }

    @property
    def airport_topic(self):
        """Return the MQTT topic for the airport"""
        return f"airport/{self.airport}"

    @property
    def mqtt_topic(self):
        """Return the MQTT topic for this gate."""
        return f"airport/{self.airport}/gate/{self.gate_number}"

    @property
    def mqttclientname(self):
        """Name of the MQTT client we will create"""
        return f"Gate_{self.gate_number}"

    @property
    def loggername(self) -> str:
        """Name of the logger"""
        return f"Gate {self.gate_number}"

    @property
    def redis_key(self) -> str:
        """Key for Redis storage"""
        return gate_redis_key(self.airport, self.gate_number)

    @property
    def state(self) -> GateState:
        """gate state"""
        return self._state

    @state.setter
    def state(self, newstate: str):
        """gate state"""
        self._state = GateState(newstate)
        self.update_gate_state_to_airport()

    def __init__(self, airport: str, gate_number: str, **kwargs):
        self.airport = airport
        self.gate_number = gate_number
        self.current_plane = None
        self._state = GateState.FREE
        self.ticks_till_exit = -1

        super().__init__(**kwargs)

        self.client.on_disconnect = lambda client, userdata, rc: client.publish(
            self.airport_topic,
            json.dumps(
                {
                    "msg_type": "gate_update",
                    "gate_number": gate_number,
                    "gate_state": GateState.CLOSED.value,
                }
            ),
        )

    def to_dict(self):
        """Convert the Gate instance to a dict representation."""
        return {
            "airport": self.airport,
            "gate_number": self.gate_number,
            "current_plane": (
                self.current_plane.to_dict() if self.current_plane else None
            ),
            "state": self.state.value,
        }

    @staticmethod
    def from_dict(data: dict, **kwargs):
        """Load the Gate state from a dict representation."""
        restored_gate = Gate(data["airport"], data["gate_number"], **kwargs)
        if data.get("current_plane"):
            restored_gate.current_plane = Plane.from_dict(data["current_plane"])
        if "state" in data:
            restored_gate.state = GateState(data["state"])
        return restored_gate

    def update_gate_state_to_airport(self):
        """Let the Airport know the gate state"""
        self.client.publish(
            self.airport_topic,
            json.dumps(
                {
                    "msg_type": "gate_update",
                    "gate_number": self.gate_number,
                    "gate_state": self.state.value,
                }
            ),
        )

    def handle_arriving_plane(self, plane: dict):
        """Handle a plane arriving at the gate from a runway."""
        self.current_plane = Plane.from_dict(plane)
        self.state = GateState.IN_USE_ARRIVING
        self.ticks_till_exit = random.randint(
            3, 5
        )  # Random time at gate between 3 and 5 ticks
        self.logger.log(
            f"Plane {self.current_plane.plane_id} is at gate for arrival; "
            + f"time at gate: {self.ticks_till_exit} ticks",
        )

    def handle_departing_plane(self, plane: dict):
        """Handle a departing plane coming to the gate on its way to a runway"""
        self.current_plane = Plane.from_dict(plane)
        self.state = GateState.IN_USE_DEPARTING
        self.ticks_till_exit = random.randint(
            3, 5
        )  # Random time at gate between 3 and 5 ticks
        self.logger.log(
            f"Plane {self.current_plane.plane_id} is at gate for departure; "
            + f"time at gate: {self.ticks_till_exit} ticks",
        )

    def handle_departure_runway_assigned(self, runway_number: str, runway_topic: str):
        """Transition plane from gate to runway for departure"""
        if self.current_plane:
            self.current_plane.state = PlaneState.ON_DEPARTURE_RUNWAY
            self.client.publish(
                runway_topic,
                json.dumps(
                    {
                        "msg_type": "plane_departing",
                        "plane": self.current_plane.to_dict(),
                    }
                ),
            )
            self.current_plane = None
        self.state = GateState.FREE

    def handle_message(self, message: dict):
        """Handle incoming plane messages at the gate."""
        if self.validate_message(["msg_type"], message):

            if message["msg_type"] == "arriving_plane":
                if self.validate_message(["plane"], message):
                    self.handle_arriving_plane(message["plane"])

            elif message["msg_type"] == "departing_plane":
                if self.validate_message(["plane"], message):
                    self.handle_departing_plane(message["plane"])

            elif message["msg_type"] == "departure_runway_assigned":
                if self.validate_message(["runway_number", "runway_topic"], message):
                    self.handle_departure_runway_assigned(
                        message["runway_number"], message["runway_topic"]
                    )

    def handle_heartbeat(self):
        """Handle heartbeat messages to update gate state."""
        if self.current_plane:
            self.logger.log(
                f"Holding plane {self.current_plane.plane_id} "
                + f"for {self.ticks_till_exit} ticks.",
            )
            self.ticks_till_exit -= 1
            if self.ticks_till_exit <= 0:
                if self.state == GateState.IN_USE_DEPARTING:
                    self.logger.log(
                        f"Plane {self.current_plane.plane_id} "
                        + "is ready to leave the gate.",
                    )
                    self.client.publish(
                        self.airport_topic,
                        json.dumps(
                            {
                                "msg_type": "requesting_departure_runway",
                                "gate": self.mqtt_topic,
                            }
                        ),
                    )

                elif self.state == GateState.IN_USE_ARRIVING:
                    self.logger.log(
                        f"Plane {self.current_plane.plane_id} "
                        + "is going back to its hangar"
                    )
                    self.current_plane = None
                    self.state = GateState.FREE


# == main
if __name__ == "__main__":
    redis_client = Redis(host=REDIS_BROKER, port=6379)
    parser = argparse.ArgumentParser(description="Gate Simulation")
    parser.add_argument("--airport", required=True, type=str, help="The airport name")
    parser.add_argument(
        "gate_number",
        type=str,
        help="The gate number to simulate (e.g., '1', '2', etc.)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    gate = construct_or_restore(
        Gate, redis_client, gate_redis_key(args.airport, args.gate_number), args
    )
    gate.client.loop_forever()
