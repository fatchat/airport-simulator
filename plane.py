"""Plane class for airport simulation."""


class Plane:
    """Plane class for airport simulation."""

    def __init__(self, plane_id):
        self.plane_id = str(plane_id)
        self.destination_gate = None
        self.state = "in_sky"
        self.ticks_on_runway = 0
        self.time_at_gate = -1

    def to_dict(self):
        """Convert the Plane instance to a dictionary for MQTT messages."""
        return {
            "plane_id": self.plane_id,
            "destination_gate": self.destination_gate,
            "state": self.state,
            "ticks_on_runway": self.ticks_on_runway,
            "time_at_gate": self.time_at_gate,
        }

    @staticmethod
    def from_dict(data: dict):
        """Initialize the Plane instance from a dictionary."""
        plane = Plane(data["plane_id"])
        plane.destination_gate = data["destination_gate"]
        plane.state = data["state"]
        plane.ticks_on_runway = data["ticks_on_runway"]
        plane.time_at_gate = data["time_at_gate"]
        return plane
