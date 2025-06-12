# Dockerized Airport Simulator

This document describes how to run the airport simulator components in Docker containers.

## Overview

The airport simulator consists of several components:

- **Airport**: Manages the overall airport, including runways and gates
- **Runway**: Handles plane arrivals and departures on runways
- **Gate**: Manages planes at gates for arrivals and departures
- **Heartbeat**: Generates timing signals for the simulation
- **DBWriter**: Writes events to a PostgreSQL database

All components communicate via MQTT and use Redis for state persistence.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Build the base image:

```bash
docker build -t airport-simulator-base -f Dockerfile.base .
```

2. Start the core services:

```bash
docker-compose up -d mosquitto redis
```

3. Start the heartbeat, dbwriter and airport-monitor-server:

```bash
docker-compose up -d heartbeat dbwriter airport-monitor-server
```

4. Start the sky:

```bash
docker-compose up -d sky
```

## Adding Components

Use the `add-component.sh` script to add airport components to the running system:

```bash
# Add an airport
./add-component.sh airport JFK

# Add a runway to the airport
./add-component.sh runway JFK 1

# Add a gate to the airport
./add-component.sh gate JFK 1
```

You can add multiple airports, runways, and gates as needed:

```bash
# Add another airport
./add-component.sh airport LAX

# Add runways to LAX
./add-component.sh runway LAX 1
./add-component.sh runway LAX 2

# Add gates to LAX
./add-component.sh gate LAX 1
./add-component.sh gate LAX 2
./add-component.sh gate LAX 3
```

## Connecting to a Remote PostgreSQL Instance

To connect to a remote PostgreSQL instance instead of the local one:

1. Edit the `.env` file and uncomment the `CONNECTION_STRING` line
2. Update the connection string with your remote PostgreSQL credentials
3. Restart the dbwriter service:

```bash
docker-compose restart dbwriter
```

## Environment Variables

The following environment variables can be set in the `.env` file:

- `CONNECTION_STRING`: PostgreSQL connection string (e.g., `postgresql://username:password@hostname:5432/dbname`)
- `POSTGRES_USER`: PostgreSQL username (default: `airport`)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: `airport`)
- `POSTGRES_DB`: PostgreSQL database name (default: `airport`)

## Network Configuration

All components communicate over a Docker network named `airport-network`. The MQTT broker (Mosquitto) and Redis server are accessible to all components on this network.

## Ports

The following ports are exposed:

- MQTT (Mosquitto): 1883
- Redis: 6379
- PostgreSQL: 5432

## Volumes

- PostgreSQL data is stored in a Docker volume named `postgres-data`
- SQL table definitions are loaded from `simulator/tabledefinitions/` into PostgreSQL on first startup
