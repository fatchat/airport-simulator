"""MQTT logger for the airport simulator."""

import paho.mqtt.client as mqtt


class Logger:
    """Logger class for the airport simulator."""

    def __init__(self, client: mqtt.Client, verbose: bool = False):
        self.client = client
        self.verbose = verbose

    def log(self, message: str):
        """Log a message to the MQTT broker."""
        if self.verbose:
            print(f"[LOG] {message}")
        self.client.publish("logs", message)
