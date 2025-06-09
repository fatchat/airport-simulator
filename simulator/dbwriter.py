"""Writes events to the SQL database"""

import os
import sys
import argparse
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    update,
    insert,
)

MQTT_BROKER = "localhost"

load_dotenv("dbwriter.env")
if not os.getenv("CONNECTION_STRING"):
    print("must set CONNECTION_STRING in dbwriter.env first")
    sys.exit(1)

engine = create_engine(os.getenv("CONNECTION_STRING"))

metadata = MetaData()

flights = Table(
    "flights",
    metadata,
    Column("flight_id", Integer, primary_key=True),
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
    Column("flight_id", Integer),
    Column("ticks", Integer),
    Column("from_state", String),
    Column("to_state", String),
)


def on_event(
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

    verbose = userdata and userdata.get("verbose")
    if verbose:
        print(message)

    # add a plane event
    if message["event_type"] == "plane-event":
        insert_statement = insert(plane_events).values(
            plane_id=message["plane_id"],
            flight_id=message["flight_id"],
            ticks=message["ticks"],
            from_state=message["from_state"],
            to_state=message["to_state"],
        )
        with engine.begin() as conn:
            conn.execute(insert_statement)

    # start a new flight object
    elif message["event_type"] == "init-flight":
        insert_statement = insert(flights).values(
            flight_id=message["flight_id"], plane_id=message["plane_id"]
        )
        with engine.begin() as conn:
            conn.execute(insert_statement)

    # update the flight object as information comes in
    elif message["event_type"] == "update-flight":
        update_stmt = update(flights).where(
            flights.c.flight_id == message["flight_id"],
            flights.c.plane_id == message["plane_id"],
        )
        update_args = dict(message)
        update_args.pop("event_type")
        update_args.pop("flight_id")
        update_args.pop("plane_id")
        update_stmt = update_stmt.values(**update_args)

        with engine.begin() as conn:
            conn.execute(update_stmt)


def main():
    """main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "dbwriter")
    mqtt_client.connect(MQTT_BROKER)
    mqtt_client.user_data_set({"verbose": args.verbose})
    mqtt_client.subscribe("events")
    mqtt_client.message_callback_add("events", on_event)
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
