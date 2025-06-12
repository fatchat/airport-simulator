"""returns state to the frontend"""

import json
import argparse
import os
from redis import Redis
from flask import Flask, jsonify, request
from flask_cors import CORS

parser = argparse.ArgumentParser(description="Gate Simulation")
parser.add_argument("--http-port", type=int, required=True, help="HTTP server port")
args = parser.parse_args()

app = Flask("Sky")
CORS(app)

redis = Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True,
)


def validate_args(request_args, required_keys: list):
    """ensures all required keys are present in request_args"""
    for key in required_keys:
        if key not in request_args:
            return False
    return True


@app.route("/state/sky", methods=["GET"])
def get_state_sky():
    """HTTP endpoint to get the current state of the sky."""
    sky = redis.get("sky")
    if not sky:
        return jsonify({"error": "Sky state not found"}), 404
    sky = json.loads(sky)
    return jsonify(sky)


@app.route("/state/airport", methods=["GET"])
def get_state_airport():
    """HTTP endpoint to get the current state of the airport."""
    if not validate_args(request.args, ["airport"]):
        return jsonify({"error": "missing parameter `airport`"}), 404

    redis_key = "airport-" + request.args["airport"]
    airport = redis.get(redis_key)
    if not airport:
        return jsonify({"error": "airport state not found for " + redis_key}), 404

    return jsonify(json.loads(airport))


@app.route("/state/runway", methods=["GET"])
def get_state_runway():
    """HTTP endpoint to get the current state of the runway."""
    if not validate_args(request.args, ["airport", "runway_number"]):
        return (
            jsonify({"error": "required parameters are `airport` and `runway_number`"}),
            404,
        )

    airport = request.args["airport"]
    runway_number = request.args["runway_number"]
    redis_key = f"airport-{airport}-runway-{runway_number}"
    runway = redis.get(redis_key)
    if not runway:
        return jsonify({"error": "runway state not found for " + redis_key}), 404

    return jsonify(json.loads(runway))


@app.route("/state/gate", methods=["GET"])
def get_state_gate():
    """HTTP endpoint to get the current state of the gate."""
    if not validate_args(request.args, ["airport", "gate_number"]):
        return (
            jsonify({"error": "required parameters are `airport` and `gate_number`"}),
            404,
        )

    airport = request.args["airport"]
    gate_number = request.args["gate_number"]
    redis_key = f"airport-{airport}-gate-{gate_number}"
    gate = redis.get(redis_key)
    if not gate:
        return jsonify({"error": "gate state not found for " + redis_key}), 404

    return jsonify(json.loads(gate))


def start_http_server():
    """Start the HTTP server to serve sky state."""
    app.run(host="0.0.0.0", port=args.http_port, threaded=True)


if __name__ == "__main__":
    start_http_server()
