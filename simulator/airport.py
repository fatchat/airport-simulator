"""Airport Simulation using MQTT"""

import json
import random
from uuid import uuid4
from typing import List, Dict

import argparse
from redis import Redis

from restorable import construct_or_restore
from airportcomponent import AirportComponent
from plane import Plane, PlaneState
from gate import GateState
from runway import RunwayState

MQTT_BROKER = "localhost"
REDIS_BROKER = "localhost"


def comma_separated_list(value: str):
    """Convert a comma-separated string into a list for argparse."""
    return value.split(",")


def airport_redis_key(airport_name: str) -> str:
    """Generate the Redis key for the airport."""
    return f"airport-{airport_name}"


class Airport(AirportComponent):
    """Representation of an airport"""

    @staticmethod
    def args_to_dict(arguments: argparse.Namespace) -> dict:
        """Convert command line arguments to a state dictionary."""
        return {"airport": arguments.airport, "runways": [], "gates": []}

    @property
    def mqtt_topic(self):
        """Return the MQTT topic for the airport"""
        return f"airport/{self.airport}"

    @property
    def mqttclientname(self):
        """Name of the MQTT client we will create"""
        return f"Airport_{self.airport}"

    @property
    def loggername(self) -> str:
        """Name of the logger"""
        return f"Airport {self.airport}"

    @property
    def redis_key(self) -> str:
        """Key for Redis storage"""
        return airport_redis_key(self.airport)

    def __init__(
        self, airport: str, runways: list | dict, gates: list | dict, **kwargs
    ):
        """Initialize the airport with a name and empty gates."""
        self.airport = airport
        if isinstance(runways, list):
            runways = {r: "free" for r in runways}
        else:
            runways = runways or {}
        if isinstance(gates, list):
            gates = {g: "free" for g in gates}
        else:
            gates = gates or {}

        self.runways: Dict[str, str] = runways
        self.gates: Dict[str, str] = gates

        self.waiting_for_departure_gate: List[Plane] = []
        self.waiting_for_arrival_gate: List[str] = []  # runway topic to notify
        self.waiting_for_departure_runway: List[str] = []  # gate topic to notify
        self.waiting_for_arrival_runway: List[Plane] = (
            []
        )  # should this be the sky topic?

        super().__init__(**kwargs)

        self.log(f"Runways: {self.runways}")
        self.log(f"Gates: {self.gates}")

    def to_dict(self):
        """Convert the Airport instance to a dict representation."""
        return {
            "airport": self.airport,
            "runways": self.runways,
            "gates": self.gates,
            "waiting_for_departure_gate": [
                plane.to_dict() for plane in self.waiting_for_departure_gate
            ],
            "waiting_for_arrival_gate": self.waiting_for_arrival_gate,
            "waiting_for_departure_runway": self.waiting_for_departure_runway,
            "waiting_for_arrival_runway": [
                plane.to_dict() for plane in self.waiting_for_arrival_runway
            ],
        }

    @staticmethod
    def from_dict(data: dict, **kwargs):
        """Load the Airport state from a dict representation."""
        restored_airport = Airport(
            data["airport"], data["runways"], data["gates"], **kwargs
        )
        if data.get("waiting_for_departure_gate"):
            restored_airport.waiting_for_departure_gate = [
                Plane.from_dict(plane_data)
                for plane_data in data["waiting_for_departure_gate"]
            ]
        if data.get("waiting_for_arrival_gate"):
            restored_airport.waiting_for_arrival_gate = data["waiting_for_arrival_gate"]

        if data.get("waiting_for_departure_runway"):
            restored_airport.waiting_for_departure_runway = data[
                "waiting_for_departure_runway"
            ]

        if data.get("waiting_for_arrival_runway"):
            restored_airport.waiting_for_arrival_runway = [
                Plane.from_dict(plane_data)
                for plane_data in data["waiting_for_arrival_runway"]
            ]
        return restored_airport

    def assign_gate_for_departure(self, gate_number: str):
        """Assign a gate for a departing plane."""
        if len(self.waiting_for_departure_gate) > 0:
            plane = self.waiting_for_departure_gate.pop(0)
            plane.start_gate = gate_number
            gate_topic = f"airport/{self.airport}/gate/{gate_number}"
            self.client.publish(
                gate_topic,
                json.dumps({"msg_type": "departing_plane", "plane": plane.to_dict()}),
            )
            self.log(f"Plane {plane.plane_id} has been assigned to gate {gate_number}")
            self.gates[gate_number] = GateState.IN_USE_DEPARTING.value
            return True
        return False

    def assign_gate_for_arrival(self, gate_number: str):
        """Assign a gate for an arriving plane."""
        if len(self.waiting_for_arrival_gate) > 0:
            runway_topic = self.waiting_for_arrival_gate.pop(0)
            self.client.publish(
                runway_topic,
                json.dumps(
                    {
                        "msg_type": "arrival_gate_assigned",
                        "gate_number": gate_number,
                        "gate_topic": f"airport/{self.airport}/gate/{gate_number}",
                    }
                ),
            )
            self.gates[gate_number] = GateState.IN_USE_ARRIVING.value
            return True
        return False

    def assign_runway_for_departure(self, runway_number: str):
        """Assign a runway to a plane waiting at a departure gate"""
        if len(self.waiting_for_departure_runway) > 0:
            gate_topic = self.waiting_for_departure_runway.pop(0)
            self.client.publish(
                gate_topic,
                json.dumps(
                    {
                        "msg_type": "departure_runway_assigned",
                        "runway_number": runway_number,
                        "runway_topic": f"airport/{self.airport}/runway/{runway_number}",
                    }
                ),
            )
            self.runways[runway_number] = RunwayState.IN_USE_DEPARTING.value
            return True
        return False

    def assign_runway_for_arrival(self, runway_number: str):
        """Assign a runway to a plane circling in the sky"""
        self.client.publish(
            "sky",
            json.dumps(
                {
                    "msg_type": "land_next_plane",
                    "airport": self.airport,
                    "runway_number": runway_number,
                }
            ),
        )
        # if there are no planes ready to land, the runway state won't change

    def handle_heartbeat(self):
        """Handle heartbeat messages to update gate state."""
        for gate_number, state in self.gates.items():
            if GateState(state) == GateState.FREE:
                self.log(f"Gate {gate_number} is free, checking for planes.")

                if random.random() < 0.5:
                    if not self.assign_gate_for_departure(gate_number):
                        self.assign_gate_for_arrival(gate_number)
                else:
                    if not self.assign_gate_for_arrival(gate_number):
                        self.assign_gate_for_departure(gate_number)

        # assign runway
        for runway_number, state in self.runways.items():
            if RunwayState(state) == RunwayState.FREE:
                self.log(f"Runway {runway_number} is free, checking for planes.")

                if random.random() < 0.5:
                    if not self.assign_runway_for_departure(runway_number):
                        self.assign_runway_for_arrival(runway_number)
                else:
                    if not self.assign_runway_for_arrival(runway_number):
                        self.assign_runway_for_departure(runway_number)

    def handle_gate_update(self, gate_number: str, gate_state: str):
        """Handle updates to gate state."""
        self.gates[gate_number] = gate_state
        self.log(f"Gate {gate_number} is now {gate_state}")

    def handle_runway_update(self, runway_number: str, runway_state: str):
        """Handle updates to runway state."""
        self.runways[runway_number] = runway_state
        self.log(f"Runway {runway_number} is now {runway_state}")

    def handle_new_plane(self, end_airport: str):
        """Handle a new plane arriving at the airport hangar."""
        plane = Plane(start_airport=self.airport, end_airport=end_airport)
        self.log(f"Plane {plane.plane_id} will depart to {plane.end_airport}")
        self.waiting_for_departure_gate.append(plane)

    def handle_register_runway(self, runway_number: str):
        """Register a new runway for this Airport"""
        self.runways[runway_number] = RunwayState.FREE.value
        self.log(f"Registered runway {runway_number}")

    def handle_register_gate(self, gate_number: str):
        """Register a new gate for this Airport"""
        self.gates[gate_number] = GateState.FREE.value
        self.log(f"Registered gate {gate_number}")

    def handle_message(self, message: dict):
        """Handle messages sent to the airport."""
        if message["msg_type"] == "gate_update":
            if self.validate_message(["gate_number", "gate_state"], message):
                self.handle_gate_update(message["gate_number"], message["gate_state"])

        elif message["msg_type"] == "runway_update":
            if self.validate_message(["runway_number", "runway_state"], message):
                self.handle_runway_update(
                    message["runway_number"], message["runway_state"]
                )

        elif message["msg_type"] == "new_plane":
            if self.validate_message(["end_airport"], message):
                self.handle_new_plane(message["end_airport"])

        elif message["msg_type"] == "requesting_arrival_gate":
            if self.validate_message(["runway_topic"], message):
                if message["runway_topic"] not in self.waiting_for_arrival_gate:
                    self.waiting_for_arrival_gate.append(message["runway_topic"])

        elif message["msg_type"] == "requesting_departure_runway":
            if self.validate_message(["gate"], message):
                if message["gate"] not in self.waiting_for_departure_runway:
                    self.waiting_for_departure_runway.append(message["gate"])

        elif message["msg_type"] == "register_runway":
            if self.validate_message(["runway_number"], message):
                self.handle_register_runway(message["runway_number"])

        elif message["msg_type"] == "register_gate":
            if self.validate_message(["gate_number"], message):
                self.handle_register_gate(message["gate_number"])


# == main
if __name__ == "__main__":
    redis_client = Redis(host=REDIS_BROKER, port=6379)
    parser = argparse.ArgumentParser(description="Airport Simulation")
    parser.add_argument("--airport", required=True, type=str, help="The airport name")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    the_airport = construct_or_restore(
        Airport, redis_client, airport_redis_key(args.airport), args
    )
    the_airport.client.loop_forever()
