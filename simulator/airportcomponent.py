"""All components must derive from AirportComponent"""

from typing import List
import json
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

    def on_heartbeat(
        self, mqtt_client, userdata, msg  # pylint:disable=unused-argument
    ):
        """Handle heartbeat messages"""
        if self.redis_client:
            self.redis_client.set(self.redis_key, json.dumps(self.to_dict()))
        payload = msg.payload.decode()
        try:
            message = json.loads(payload)
            self.ticks = int(message.get("ticks", 0))
        except json.decoder.JSONDecodeError:
            self.ticks = 0
        self.handle_heartbeat()

    @abstractmethod
    def handle_heartbeat(self):
        """Child-specific implementations"""

    @property
    @abstractmethod
    def mqtt_topic(self) -> str:
        """MQTT topic for this object"""

    @abstractmethod
    def handle_message(self, message: dict):
        """Client-specific implementation"""

    def on_message(self, mqtt_client, userdata, msg):  # pylint:disable=unused-argument
        """Handler for mqtt_topic"""
        payload = msg.payload.decode()
        try:
            message = json.loads(payload)
        except json.decoder.JSONDecodeError:
            self.error(f"received non-json message: [{payload}]")
            return
        if "msg_type" not in message:
            self.error("Message does not contain 'msg_type'")
            self.error(message)
            return
        self.handle_message(message)

    @property
    @abstractmethod
    def loggername(self) -> str:
        """Name of the logger"""

    def log(self, message: str):
        """logs a message"""
        self.logger.log(self.logger.tag(message, f"ticks={self.ticks}"))

    def error(self, message: str):
        """logs a message"""
        self.logger.error(self.logger.tag(message, f"ticks={self.ticks}"))

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
            self.error("Missing keys in message: " + ", ".join(missing_keys))
            self.error(message)
            return False
        return True

    def __init__(self, **kwargs):
        """constructor"""
        self.ticks = -1
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.mqttclientname)
        self.client.connect(MQTT_BROKER)
        self.logger = Logger(
            self.loggername, self.client, verbose=kwargs.get("verbose", False)
        )
        self.client.subscribe("heartbeat")
        self.client.message_callback_add("heartbeat", self.on_heartbeat)

        self.client.subscribe(self.mqtt_topic)
        self.client.message_callback_add(self.mqtt_topic, self.on_message)

        self.redis_client = None
        self.log("Initialized")
