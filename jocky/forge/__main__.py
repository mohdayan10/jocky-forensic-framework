"""Entry point for: python3 -m jocky.forge"""

import argparse
import os
import sys

from ..compiler.pipeline import CompilerPipeline
from .builder import ForgeBuilder


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.forge",
        description="JOCKY Forge — Polymorphic build pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    # forge build — single build
    build_p = sub.add_parser("build", help="Build a single agent binary")
    build_p.add_argument("file", help="Path to .jky source file")
    build_p.add_argument("--output", "-o", default="agent.bin", help="Output binary path")

    # forge deploy — multi-target
    deploy_p = sub.add_parser("deploy", help="Deploy to multiple targets")
    deploy_p.add_argument("file", help="Path to .jky source file")
    deploy_p.add_argument("--targets", "-t", required=True, help="Comma-separated host list")
    deploy_p.add_argument("--output-dir", default="/tmp/jocky_forge_builds",
                          help="Output directory for builds")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)

    with open(args.file) as f:
        source = f.read()

    filename = os.path.basename(args.file)

    if args.command == "build":
        import hashlib
        import secrets

        pipeline = CompilerPipeline(verbose=True)
        result = pipeline.compile(source, filename)
        if not result.success:
            print(f"\n[BUILD] Compilation failed.")
            sys.exit(1)

        output = args.output
        mutation_seed = secrets.token_hex(16)
        build_content = f"JOCKY_AGENT_v1\n{mutation_seed}\n{result.jir_json}"
        build_hash = hashlib.sha256(build_content.encode()).hexdigest()

        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            f.write(build_content)

        print(f"\n[BUILD]    Generating agent binary...              OK")
        print(f"[BUILD]    Output:     {output}")
        print(f"[BUILD]    SHA-256:    {build_hash}")
        print(f"[BUILD]    Mutation:   {mutation_seed[:16]}...")
        print(f"[BUILD]    Build complete.")

    elif args.command == "deploy":
        targets = [t.strip() for t in args.targets.split(",")]
        builder = ForgeBuilder(output_dir=args.output_dir)
        builder.deploy(source, filename, targets)


if __name__ == "__main__":
    main()
