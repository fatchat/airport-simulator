"""returns state to the frontend"""

import json
import argparse
from redis import Redis
from flask import Flask, jsonify, request
from flask_cors import CORS

parser = argparse.ArgumentParser(description="Gate Simulation")
parser.add_argument("--http-port", type=int, required=True, help="HTTP server port")
args = parser.parse_args()

app = Flask("Sky")
CORS(app)

redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)


@app.route("/state/sky", methods=["GET"])
def get_state_sky():
    """HTTP endpoint to get the current state of the sky."""
    sky = redis.get("sky")
    if not sky:
        return jsonify({"error": "Sky state not found"}), 404
    sky = json.loads(sky)
    return jsonify(sky)


@app.route("/state/runway", methods=["GET"])
def get_state_runway():
    """HTTP endpoint to get the current state of the runway."""
    runway = redis.get("runway")
    if not runway:
        return jsonify({"error": "runway state not found"}), 404
    runway = json.loads(runway)
    return jsonify(runway)


@app.route("/state/gate", methods=["GET"])
def get_state_gate():
    """HTTP endpoint to get the current state of the gate."""
    gate = redis.get("gate-" + request.args.get("gate_number", "1"))
    if not gate:
        return jsonify({"error": "gate state not found"}), 404
    gate = json.loads(gate)
    return jsonify(gate)


def start_http_server():
    """Start the HTTP server to serve sky state."""
    app.run(host="0.0.0.0", port=args.http_port, threaded=True)


if __name__ == "__main__":
    start_http_server()
