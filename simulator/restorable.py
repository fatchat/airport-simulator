"""Functions for restorable objects"""

import argparse
import json
from redis import Redis


def construct_or_restore(
    cls, redis_client: Redis, redis_key: str, arguments: argparse.Namespace
):
    """Construct a Runway instance or restore from a saved state."""
    saved_state = redis_client.get(redis_key)
    if saved_state:
        print("Restoring saved state from Redis...")
        return cls.from_dict(
            json.loads(saved_state.decode()), verbose=arguments.verbose
        )

    return cls.from_dict(
        cls.args_to_dict(arguments),
        verbose=arguments.verbose,
    )
