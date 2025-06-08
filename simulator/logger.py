"""MQTT logger for the airport simulator."""

import paho.mqtt.client as mqtt


class Logger:
    """Logger class for the airport simulator."""

    def __init__(self, name: str, mqtt_client: mqtt.Client, verbose: bool = False):
        self.name = name
        self.mqtt_client = mqtt_client
        self.verbose = verbose

    def tag(self, message: str, tag: str) -> str:
        """tags a message"""
        return f"[{tag}] {message}"

    def log(self, message: str):
        """Log a message to the MQTT broker."""
        message = self.tag(message, self.name)
        if self.verbose:
            print(message)
        self.mqtt_client.publish("logs", message)

    def error(self, message: str):
        """Log an error message to the MQTT broker."""
        self.log(self.tag(message, "ERROR!"))
