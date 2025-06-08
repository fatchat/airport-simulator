"""Runway module for handling plane arrivals and sending them to gates."""

import json
import random
from enum import Enum

import argparse
from redis import Redis

from restorable import construct_or_restore
from airportcomponent import AirportComponent
from plane import Plane, PlaneState

REDIS_BROKER = "localhost"


class RunwayState(Enum):
    """Enumeration for runway states."""

    FREE = "free"
    IN_USE_DEPARTING = "in-use-departing"
    IN_USE_ARRIVING = "in-use-arriving"


def runway_redis_key(airport: str, runway_number: str):
    """key for storing this runway in redis"""
    return f"airport-{airport}-runway-{runway_number}"


class Runway(AirportComponent):
    """Representation of a runway at an airport."""

    RUNWAY_MIN_TICKS = 3  # Minimum ticks a plane stays on the runway
    RUNWAY_MAX_TICKS = 10

    @staticmethod
    def args_to_dict(arguments: argparse.Namespace) -> dict:
        """Convert command line arguments to a state dictionary."""
        return {
            "airport": arguments.airport,
            "runway_number": arguments.runway_number,
        }

    @property
    def airport_topic(self):
        """Return the MQTT topic for the airport"""
        return f"airport/{self.airport}"

    @property
    def mqtt_topic(self):
        """Return the MQTT topic for this runway."""
        return f"airport/{self.airport}/runway/{self.runway_number}"

    @property
    def mqttclientname(self):
        """Name of the MQTT client we will create"""
        return f"Runway_{self.runway_number}"

    @property
    def redis_key(self) -> str:
        """Name of key for redis storage"""
        return runway_redis_key(self.airport, self.runway_number)

    @property
    def loggername(self) -> str:
        """Name of the logger"""
        return f"Airport/{self.airport}/Runway/{self.runway_number}"

    @property
    def state(self) -> RunwayState:
        """runway state"""
        return self._state

    @state.setter
    def state(self, newstate: str):
        """runway state"""
        self._state = RunwayState(newstate)
        self.update_runway_state_to_airport()

    def __init__(self, airport: str, runway_number: str, **kwargs):
        """Runway listens for planes arriving and sends them to gates after 3 ticks."""
        self.airport = airport
        self.runway_number = runway_number
        self.current_plane = None
        self._state = RunwayState.FREE
        self.ticks_till_exit = -1
        self.topic_to_notify_on_exit = None

        super().__init__(**kwargs)

    def to_dict(self):
        """Convert the Runway instance to a JSON representation."""
        return {
            "airport": self.airport,
            "runway_number": self.runway_number,
            "current_plane": (
                self.current_plane.to_dict() if self.current_plane else None
            ),
            "state": self.state.value,
            "ticks_till_exit": self.ticks_till_exit,
            "topic_to_notify_on_exit": self.topic_to_notify_on_exit,
        }

    @staticmethod
    def from_dict(data, **kwargs):
        """Load the Runway state from a JSON representation."""
        restored_runway = Runway(data["airport"], data["runway_number"], **kwargs)
        if data.get("current_plane"):
            restored_runway.current_plane = Plane.from_dict(data["current_plane"])
        restored_runway.ticks_till_exit = data.get("ticks_till_exit", -1)
        restored_runway.topic_to_notify_on_exit = data.get("topic_to_notify_on_exit")
        if "state" in data:
            restored_runway.state = RunwayState(data["state"])
        return restored_runway

    def update_runway_state_to_airport(self):
        """Let the Airport know the runway state"""
        self.client.publish(
            self.airport_topic,
            json.dumps(
                {
                    "msg_type": "runway_update",
                    "runway_number": self.runway_number,
                    "runway_state": self.state.value,
                }
            ),
        )

    def handle_plane_arriving(self, plane: dict):
        """Handle the landing of a plane"""
        if self.current_plane:
            self.logger.log(
                f"ERROR!!! Plane {plane['plane_id']} arrived but runway "
                + f"is occupied by {self.current_plane['plane_id']}",
            )
            return
        if self.state != RunwayState.FREE:
            self.logger.log("ERROR: Runway in use")
            return

        self.current_plane = Plane.from_dict(plane)
        self.ticks_till_exit = random.randint(
            Runway.RUNWAY_MIN_TICKS, Runway.RUNWAY_MAX_TICKS
        )
        self.current_plane.state = PlaneState.ON_ARRIVAL_RUNWAY
        self.state = RunwayState.IN_USE_ARRIVING
        self.topic_to_notify_on_exit = None  # don't have a gate yet

        self.client.publish(
            self.airport_topic,
            json.dumps(
                {
                    "msg_type": "requesting_arrival_gate",
                    "runway_topic": self.mqtt_topic,
                }
            ),
        )
        self.logger.log(
            f"Plane {plane['plane_id']} arrived on runway, waiting for gate"
        )

    def handle_arrival_gate_assigned(self, gate_topic: str, gate_number: str):
        """Handle the assignment of an arrival gate"""
        self.topic_to_notify_on_exit = gate_topic
        self.logger.log(
            f"Runway {self.runway_number} received gate assignment: {self.topic_to_notify_on_exit}"
        )
        if self.current_plane:
            self.current_plane.end_gate = gate_number
            self.current_plane.state = PlaneState.ON_ARRIVAL_RUNWAY
            self.state = RunwayState.IN_USE_ARRIVING
            self.advance_plane()
        else:
            self.logger.log("No plane on runway to advance")

    def handle_plane_departing(self, plane: dict):
        """Handle a plane departing from this runway"""
        if self.state != RunwayState.FREE:
            self.logger.log("ERROR: Runway in use")
            return
        self.state = RunwayState.IN_USE_DEPARTING
        self.current_plane = Plane.from_dict(plane)
        self.current_plane.state = PlaneState.ON_DEPARTURE_RUNWAY
        self.ticks_till_exit = random.randint(
            Runway.RUNWAY_MIN_TICKS, Runway.RUNWAY_MAX_TICKS
        )
        self.topic_to_notify_on_exit = "sky"

    def handle_message(self, message: dict):
        """Handle plane arrivals on the runway."""
        if message["msg_type"] == "plane_arrival":
            if self.validate_message(["plane"], message):
                self.handle_plane_arriving(message["plane"])

        elif message["msg_type"] == "arrival_gate_assigned":
            if self.validate_message(["gate_topic", "gate_number"], message):
                self.handle_arrival_gate_assigned(
                    message["gate_topic"], message["gate_number"]
                )

        elif message["msg_type"] == "plane_departing":
            if self.validate_message(["plane"], message):
                self.handle_plane_departing(message["plane"])

    def advance_plane(self):
        """Advance the plane on the runway, check if it can be sent to a gate."""
        if self.state == RunwayState.FREE or not self.current_plane:
            return

        self.ticks_till_exit -= 1

        if self.ticks_till_exit > 0:
            self.logger.log(
                f"Plane {self.current_plane.plane_id} still on runway, "
                + f"ticks: {self.ticks_till_exit}",
            )
            return

        if (
            self.state == RunwayState.IN_USE_ARRIVING
            and not self.topic_to_notify_on_exit
        ):
            self.logger.log(
                f"No gate assigned for plane {self.current_plane.plane_id} "
                + f"on runway {self.runway_number}"
            )
            return

        if self.state == RunwayState.IN_USE_DEPARTING:
            self.current_plane.state = PlaneState.IN_SKY
            self.client.publish(
                self.topic_to_notify_on_exit,
                json.dumps(
                    {
                        "msg_type": "plane_departure",
                        "plane": self.current_plane.to_dict(),
                    }
                ),
            )
        self.topic_to_notify_on_exit = None
        self.current_plane = None

        if self.state == RunwayState.IN_USE_ARRIVING and self.topic_to_notify_on_exit:
            self.client.publish(
                self.topic_to_notify_on_exit,
                json.dumps(
                    {
                        "msg_type": "arriving_plane",
                        "plane": self.current_plane.to_dict(),
                    }
                ),
            )
            self.logger.log(
                f"Sent plane {self.current_plane.plane_id} to {self.topic_to_notify_on_exit}"
            )
            self.topic_to_notify_on_exit = None
            self.current_plane = None

        self.state = RunwayState.FREE

    def handle_heartbeat(self):
        """Handle heartbeat messages to advance the runway state."""
        if self.current_plane:
            self.advance_plane()

        if self.current_plane is None:
            self.logger.log("Ready for next plane")


if __name__ == "__main__":
    redis_client = Redis(host=REDIS_BROKER, port=6379)
    parser = argparse.ArgumentParser(description="Gate Simulation")
    parser.add_argument("--airport", required=True, type=str, help="The airport name")
    parser.add_argument(
        "--runway-number", required=True, type=str, help="The runway number"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    the_runway = construct_or_restore(
        Runway,
        redis_client,
        runway_redis_key(args.airport, args.runway_number),
        args,
    )
    the_runway.client.loop_forever()
