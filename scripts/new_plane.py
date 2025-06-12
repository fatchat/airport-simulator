"""adds a plane and flight"""

import argparse
import json
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("from_airport")
    parser.add_argument("to_airport")
    args = parser.parse_args()
    topic = "airport/" + args.from_airport
    cmd = [
        "mosquitto_pub",
        "-t",
        topic,
        "-m",
        json.dumps({"msg_type": "new_plane", "end_airport": args.to_airport}),
    ]
    print(cmd)
    subprocess.check_call(cmd)
