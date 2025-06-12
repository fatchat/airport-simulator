#!/bin/bash

# add-component.sh
# Usage: ./add-component.sh [component-type] [airport] [number]
# Example: ./add-component.sh runway JFK 3

COMPONENT_TYPE=$1
AIRPORT=$2
NUMBER=$3

if [ "$COMPONENT_TYPE" == "airport" ]; then
  docker-compose run -d --name "airport-$AIRPORT" airport --airport $AIRPORT --verbose
elif [ "$COMPONENT_TYPE" == "runway" ]; then
  docker-compose run -d --name "runway-$AIRPORT-$NUMBER" runway --airport $AIRPORT --runway-number $NUMBER --verbose
elif [ "$COMPONENT_TYPE" == "gate" ]; then
  docker-compose run -d --name "gate-$AIRPORT-$NUMBER" gate --airport $AIRPORT --gate-number $NUMBER --verbose
else
  echo "Unknown component type: $COMPONENT_TYPE"
  echo "Usage: ./add-component.sh [component-type] [airport] [number]"
  exit 1
fi
