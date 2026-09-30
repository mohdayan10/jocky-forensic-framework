"""Entry point for: python3 -m jocky.dispatch"""

import argparse
import os
import sys

from ..console.dispatch import CommandConsole
from ..compiler.pipeline import CompilerPipeline
from ..forge.builder import ForgeBuilder


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.dispatch",
        description="JOCKY Dispatch — Multi-endpoint investigation deployment",
    )
    parser.add_argument("file", help="Path to .jky source file")
    parser.add_argument("--targets", "-t", required=True,
                        help="Comma-separated host list or ALL")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)

    with open(args.file) as f:
        source = f.read()

    filename = os.path.basename(args.file)

    # Compile
    pipeline = CompilerPipeline(verbose=True)
    result = pipeline.compile(source, filename)
    if not result.success:
        print("[DISPATCH] Compilation failed.")
        sys.exit(1)

    case_id = result.jir.case_id if result.jir else "UNKNOWN"

    if args.targets.upper() == "ALL":
        targets = ["HOST-01", "HOST-02", "HOST-03"]
    else:
        targets = [t.strip() for t in args.targets.split(",")]

    # Forge per-host builds
    print()
    builder = ForgeBuilder(output_dir="/tmp/jocky_forge_builds")
    builder.deploy(source, filename, targets)

    # Dispatch
    print()
    console = CommandConsole()
    console.dispatch_verbose(case_id, targets)


if __name__ == "__main__":
    main()
