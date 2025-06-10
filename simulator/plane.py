"""Plane class for airport simulation."""

from enum import Enum
from uuid import uuid4
import json


class PlaneState(Enum):
    """Enumeration for plane states."""

    IN_HANGAR = "in_hangar"
    AT_DEPARTURE_GATE = "at_departure_gate"
    ON_DEPARTURE_RUNWAY = "on_departure_runway"
    IN_SKY = "in_sky"
    CIRCLING = "circling"  # do we need this
    ON_ARRIVAL_RUNWAY = "on_arrival_runway"
    AT_ARRIVAL_GATE = "at_arrival_gate"


class Plane:
    """Plane class for airport simulation."""

    def __init__(self, start_airport: str, end_airport: str):
        self.plane_id = str(uuid4().hex[:12])
        self.flight_id = str(uuid4().hex[:12])

        self.start_airport = start_airport
        self.end_airport = end_airport

        # do we need these?
        self.start_gate = None
        self.end_gate = None

        self.state = PlaneState.IN_HANGAR

        self.ticks_in_sky = -1  # filled by Sky when plane is in the sky

    def to_dict(self):
        """Convert the Plane instance to a dictionary for MQTT messages."""
        return {
            "plane_id": self.plane_id,
            "flight_id": self.flight_id,
            "start_airport": self.start_airport,
            "end_airport": self.end_airport,
            "start_gate": self.start_gate,
            "end_gate": self.end_gate,
            "state": self.state.value,
            "ticks_in_sky": self.ticks_in_sky,
        }

    @staticmethod
    def from_dict(data: dict):
        """Initialize the Plane instance from a dictionary."""
        plane = Plane(data["start_airport"], data["end_airport"])
        plane.plane_id = data["plane_id"]
        plane.flight_id = data.get("flight_id")
        plane.start_gate = data["start_gate"]
        plane.end_gate = data["end_gate"]
        plane.state = PlaneState(data["state"])
        plane.ticks_in_sky = data["ticks_in_sky"]
        return plane

    def set_state(self, new_state: PlaneState, mqtt_client, ticks: int):
        """on state changes, send state to dbwriter"""
        mqtt_client.publish(
            "events",
            json.dumps(
                {
                    "event_type": "plane-event",
                    "plane_id": self.plane_id,
                    "flight_id": self.flight_id,
                    "ticks": ticks,
                    "from_state": self.state.value,
                    "to_state": new_state.value,
                }
            ),
        )
        self.state = new_state

    def init_flight(self, mqtt_client):
        """update a flight for this plane"""
        mqtt_client.publish(
            "events",
            json.dumps(
                {
                    "event_type": "init-flight",
                    "flight_id": self.flight_id,
                    "plane_id": self.plane_id,
                }
            ),
        )

    def update_flight(self, mqtt_client, **kwargs):
        """update a flight for this plane"""
        mqtt_client.publish(
            "events",
            json.dumps(
                {
                    "event_type": "update-flight",
                    "flight_id": self.flight_id,
                    "plane_id": self.plane_id,
                    **kwargs,
                }
            ),
        )
