"""Entry point for: python3 -m jocky.beacon"""

import argparse
from .beacon import BeaconManager


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.beacon",
        description="JOCKY Beacon — Cloud-routed communication",
    )
    parser.add_argument("--host", required=True, help="Target host")
    parser.add_argument("--cloud", default="azure", choices=["azure", "aws"],
                        help="Cloud provider (default: azure)")

    args = parser.parse_args()
    manager = BeaconManager()
    manager.establish_verbose(args.host, args.cloud)


if __name__ == "__main__":
    main()
