"""Plane class for airport simulation."""

from enum import Enum


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

    def __init__(self, plane_id: str, start_airport: str, end_airport: str):
        self.plane_id = str(plane_id)

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
        plane = Plane(data["plane_id"], data["start_airport"], data["end_airport"])
        plane.start_gate = data["start_gate"]
        plane.end_gate = data["end_gate"]
        plane.state = PlaneState(data["state"])
        plane.ticks_in_sky = data["ticks_in_sky"]
        return plane
