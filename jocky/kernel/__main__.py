"""Entry point for: python3 -m jocky.kernel"""

import argparse
from .collector import KernelCollector


OPERATION_MAP = {
    "HIDDEN_PROCESS": "HIDDEN_PROCESS_DELTA",
    "HIDDEN_PROCESS_DELTA": "HIDDEN_PROCESS_DELTA",
    "HOOK_STATE": "HOOK_STATE",
    "BYOVD": "DRIVER_INTELLIGENCE",
    "DRIVER_INTELLIGENCE": "DRIVER_INTELLIGENCE",
}


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.kernel",
        description="JOCKY Kernel Layer — Kernel-level forensic collection",
    )
    sub = parser.add_subparsers(dest="command")

    collect_p = sub.add_parser("collect", help="Run a kernel collection operation")
    collect_p.add_argument("--host", required=True, help="Target host")
    collect_p.add_argument("--op", "--operation", required=True,
                           choices=list(OPERATION_MAP.keys()),
                           help="Kernel operation to run")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    operation = OPERATION_MAP[args.op]
    collector = KernelCollector()
    collector.collect_verbose(args.host, operation)


if __name__ == "__main__":
    main()
