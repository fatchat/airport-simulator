"""Airport Simulation using MQTT"""

import json
from typing import List, Dict
import random
import argparse
from redis import Redis

from restorable import construct_or_restore
from airportcomponent import AirportComponent
from plane import Plane, PlaneState

REDIS_BROKER = "localhost"


class Sky(AirportComponent):
    """Representation of the sky where planes fly."""

    @staticmethod
    def args_to_dict(arguments: argparse.Namespace) -> dict:
        """Convert command line arguments to a state dictionary."""
        return {}

    @property
    def mqtt_topic(self):
        """Return the MQTT topic for the Sky."""
        return "sky"

    @property
    def mqttclientname(self):
        """Name of the MQTT client we will create"""
        return "Sky"

    @property
    def loggername(self) -> str:
        """Name of the logger"""
        return "Sky"

    @property
    def redis_key(self) -> str:
        """Key for Redis storage"""
        return "sky"

    def __init__(self, **kwargs):
        self.plane_queues: Dict[str, List[Plane]] = {}
        self.planes_flying: List[Plane] = []

        super().__init__(**kwargs)

    def to_dict(self):
        """Convert the Sky instance to a JSON representation."""
        return {
            "plane_queues": {
                airport: [plane.to_dict() for plane in planes]
                for airport, planes in self.plane_queues.items()
            },
            "planes_flying": [plane.to_dict() for plane in self.planes_flying],
        }

    @staticmethod
    def from_dict(data, **kwargs):
        """Load the Sky state from a JSON representation."""
        restored_sky = Sky(**kwargs)
        for airport, plane_queue in data.get("plane_queues", {}).items():
            restored_sky.plane_queues[airport] = [
                Plane.from_dict(plane) for plane in plane_queue
            ]
        restored_sky.planes_flying = [
            Plane.from_dict(plane) for plane in data.get("planes_flying", [])
        ]
        return restored_sky

    def handle_message(self, message: dict):
        """runway requests next plane"""
        if self.validate_message(["msg_type"], message):

            if message["msg_type"] == "land_next_plane":

                if self.validate_message(["airport", "runway_number"], message):
                    airport = message["airport"]
                    self.log(f"Request to send next plane received from {airport}.")

                    if self.plane_queues.get(airport):

                        runway_number = message["runway_number"]
                        plane: Plane = self.plane_queues[airport].pop(0)
                        runway_topic = f"airport/{airport}/runway/{runway_number}"
                        self.client.publish(
                            runway_topic,
                            json.dumps(
                                {
                                    "msg_type": "plane_arrival",
                                    "plane": plane.to_dict(),
                                }
                            ),
                        )
                        self.log(f"Sent plane {plane.plane_id} to {runway_topic}")
                    else:
                        self.log(f"No planes available to land at {airport}")

            elif message["msg_type"] == "plane_departure":

                if self.validate_message(["plane"], message):
                    plane_data = message["plane"]
                    if plane_data:

                        plane = Plane.from_dict(plane_data)
                        plane.ticks_in_sky = random.randint(5, 10)
                        plane.state = PlaneState.IN_SKY
                        self.planes_flying.append(plane)

                        self.log(
                            f"Plane {plane.plane_id} is departing to {plane.end_airport} "
                            + f"and will be in the sky for {plane.ticks_in_sky} ticks."
                        )

                        if plane.end_airport not in self.plane_queues:
                            self.plane_queues[plane.end_airport] = []
                    else:
                        self.log("No plane data provided in departure message")

    def handle_heartbeat(self):
        """Handle heartbeat messages to add new planes."""
        for plane in list(self.planes_flying):
            if plane.ticks_in_sky <= 0:
                plane.state = PlaneState.CIRCLING
                self.plane_queues[plane.end_airport].append(plane)
                self.planes_flying.remove(plane)
                self.log(
                    f"Plane {plane.plane_id} has started circling to land at {plane.end_airport}."
                )
            else:
                plane.ticks_in_sky -= 1
                self.log(
                    f"Plane {plane.plane_id} is still in the sky, "
                    + f"{plane.ticks_in_sky} ticks remaining."
                )


if __name__ == "__main__":
    redis_client = Redis(host=REDIS_BROKER, port=6379)
    parser = argparse.ArgumentParser(description="Gate Simulation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    sky = construct_or_restore(Sky, redis_client, "sky", parser.parse_args())
    sky.client.loop_forever()
