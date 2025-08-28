import os
import sys
import argparse
import pathlib
import json

import Server

def verify_config_path(config_path):
    # None check
    if not config_path:
        return False

    # check if file exists and can be read
    if os.path.exists(config_path) and os.access(config_path, os.R_OK):
        return True

    return False

# main entry point for the server
if __name__ == "__main__":

    #
    # parse cli arguments
    #

    # setup ArgumentParser
    parser = argparse.ArgumentParser(
        prog="muserve-server",
        description="Muserve Server is the backend to the Muserve application",
    )

    # add all arguments
    parser.add_argument(
        "--conf",
        help="specify the path to a config file",
    )

    # get the parsed arguments
    args = parser.parse_args()

    #
    # order locations to check in order of greatest precedence
    #

    # only for default locations
    expected_config_name = "muserve.json" 

    config_locations = []

    # --conf=[CONF] flag
    config_locations.append(
        pathlib.Path(args.conf) if args.conf else None
    )

    # $HOME/.config/muserve/muserve.json
    config_locations.append(
        pathlib.Path.home() / ".config" / "muserve" / expected_config_name,
    )

    # ./muserve.json
    config_locations.append(
        pathlib.Path(".") / expected_config_name
    )

    #
    # check which config file to read from
    #

    config_path = None
    for location in config_locations:
        if verify_config_path(location):
            config_path = location
            break

    # if no location was found, exit with an error
    if not config_path:
        # TODO: make a better error for this condition
        print("error: could not find a valid config path", file=sys.stderr)
        sys.exit(1)

    #
    # verify config
    #

    # get raw file text
    with open(config_path, encoding="utf-8") as f:
        config_string = f.read()

    # ensure config is valid json
    try:
        config = json.loads(config_string)
    except json.JSONDecodeError as err:
        # TODO: make a better error for this condition
        print(f"error while decoding json: {err}", file=sys.stderr)
        sys.exit(1)

    #
    # start the server
    #

    # TODO: use config to edit server parameters

    server = Server.Server()

    server.start()

    # server.start() starts the server in a thread, while(True) keeps the app
    # running
    while (True):
        pass
