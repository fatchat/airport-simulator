"""All components must derive from AirportComponent"""

from typing import List
from abc import ABC, abstractmethod
import argparse
import paho.mqtt.client as mqtt

from logger import Logger

MQTT_BROKER = "localhost"


class AirportComponent(ABC):
    """Interface for components in the messaging system"""

    @staticmethod
    @abstractmethod
    def args_to_dict(arguments: argparse.Namespace) -> dict:
        """Convert command line arguments to a state dictionary."""

    @abstractmethod
    def to_dict(self):
        """Return a dict representation"""

    @staticmethod
    @abstractmethod
    def from_dict(data: dict, **kwargs):
        """Construct object from dict representation"""

    @property
    @abstractmethod
    def mqttclientname(self) -> str:
        """Name of the MQTT client we will create"""

    @abstractmethod
    def on_heartbeat(self, mqtt_client, userdata, msg):
        """Handle heartbeat messages"""

    @property
    @abstractmethod
    def mqtt_topic(self) -> str:
        """MQTT topic for this object"""

    @abstractmethod
    def on_message(self, mqtt_client, userdata, msg):
        """Handler for mqtt_topic"""

    @property
    @abstractmethod
    def loggername(self) -> str:
        """Name of the logger"""

    @property
    @abstractmethod
    def redis_key(self) -> str:
        """Key for Redis storage"""

    def validate_message(self, required_keys: List[str], message: dict):
        """Validate that the message contains all required keys."""
        missing_keys = []
        for key in required_keys:
            if key not in message:
                missing_keys.append(key)
        if missing_keys:
            self.logger.log("ERROR Missing keys in message: " + ", ".join(missing_keys))
            self.logger.log(message)
            return False
        return True

    def __init__(self, **kwargs):
        """constructor"""
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.mqttclientname)
        self.client.connect(MQTT_BROKER)
        self.logger = Logger(
            self.loggername, self.client, verbose=kwargs.get("verbose", False)
        )
        self.client.subscribe("heartbeat")
        self.client.message_callback_add("heartbeat", self.on_heartbeat)

        self.client.subscribe(self.mqtt_topic)
        self.client.message_callback_add(self.mqtt_topic, self.on_message)

        self.logger.log("Initialized")
