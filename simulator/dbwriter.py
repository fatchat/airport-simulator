"""Writes events to the SQL database"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    DateTime,
    update,
    insert,
)

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")

SECONDS_PER_TICKS = int(os.environ.get("SECONDS_PER_TICKS", "10"))

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")
if not CONNECTION_STRING:
    print("CONNECTION_STRING environment variable must be set")
    sys.exit(1)


class DBWriter:
    """Client to write to the database"""

    metadata = MetaData()

    flights = Table(
        "flights",
        metadata,
        Column("flight_id", String, primary_key=True),
        Column("plane_id", String, primary_key=True),
        Column("from_airport", String),
        Column("to_airport", String),
        Column("from_runway", String),
        Column("to_runway", String),
        Column("from_gate", String),
        Column("to_gate", String),
    )

    plane_events = Table(
        "plane_events",
        metadata,
        Column("plane_id", String),
        Column("flight_id", String),
        Column("ticks", Integer),
        Column("event_time", DateTime),
        Column("from_state", String),
        Column("to_state", String),
    )

    def __init__(self, **kwargs):
        self.engine = create_engine(CONNECTION_STRING)
        self.starttime = kwargs["starttime"]
        self.verbose = kwargs.get("verbose", False)

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "dbwriter")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.connect(MQTT_BROKER)

    def on_connect(self, mqtt_client, userdata, connect_flags, reason_code, properties):
        """on connection to the broker"""
        if reason_code == 0:
            self.mqtt_client.subscribe("events")
            self.mqtt_client.message_callback_add("events", self.on_event)
        else:
            raise RuntimeError("failed to connect to mqtt broker")

    def on_event(
        self,
        mqtt_client: mqtt.Client,  # pylint:disable=unused-argument
        userdata,  # pylint:disable=unused-argument
        msg: mqtt.MQTTMessage,
    ):
        """event handler"""
        payload = msg.payload.decode()
        try:
            message = json.loads(payload)
        except json.decoder.JSONDecodeError:
            print("Error decoding message " + payload)
            return

        if self.verbose:
            print(message)

        # add a plane event
        if message["event_type"] == "plane-event":
            event_time = self.starttime + timedelta(
                seconds=SECONDS_PER_TICKS * int(message["ticks"])
            )
            insert_statement = insert(DBWriter.plane_events).values(
                plane_id=message["plane_id"],
                flight_id=message["flight_id"],
                ticks=message["ticks"],
                event_time=event_time,
                from_state=message["from_state"],
                to_state=message["to_state"],
            )
            with self.engine.begin() as conn:
                conn.execute(insert_statement)

        # start a new flight object
        elif message["event_type"] == "init-flight":
            insert_statement = insert(DBWriter.flights).values(
                flight_id=message["flight_id"], plane_id=message["plane_id"]
            )
            with self.engine.begin() as conn:
                conn.execute(insert_statement)

        # update the flight object as information comes in
        elif message["event_type"] == "update-flight":
            update_stmt = update(DBWriter.flights).where(
                DBWriter.flights.c.flight_id == message["flight_id"],
                DBWriter.flights.c.plane_id == message["plane_id"],
            )
            update_args = dict(message)
            update_args.pop("event_type")
            update_args.pop("flight_id")
            update_args.pop("plane_id")
            update_stmt = update_stmt.values(**update_args)

            with self.engine.begin() as conn:
                conn.execute(update_stmt)


def main():
    """main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("starttime")
    args = parser.parse_args()

    try:
        starttime = datetime.strptime(args.starttime, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        print("starttime must be of the format %Y-%m-%dT%H:%M:%S")
        return
    dbwriter = DBWriter(verbose=args.verbose, starttime=starttime)
    dbwriter.mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
