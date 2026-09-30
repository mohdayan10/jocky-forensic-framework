"""JOCKY CLI — Command-line interface for the JOCKY forensic framework."""

from __future__ import annotations

import argparse
import sys
import os

from .compiler.pipeline import CompilerPipeline, CompileResult
from .compiler.policy.validator import InvestigatorCert


BANNER = r"""
     ██╗ ██████╗  ██████╗██╗  ██╗██╗   ██╗
     ██║██╔═══██╗██╔════╝██║ ██╔╝╚██╗ ██╔╝
     ██║██║   ██║██║     █████╔╝  ╚████╔╝
██   ██║██║   ██║██║     ██╔═██╗   ╚██╔╝
╚█████╔╝╚██████╔╝╚██████╗██║  ██╗   ██║
 ╚════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝
  From Program to Verified Investigation
"""


def cmd_compile(args):
    """Handle: jocky compile <file> [--verbose] [--emit-jir]"""
    filepath = args.file

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r") as f:
        source = f.read()

    filename = os.path.basename(filepath)
    pipeline = CompilerPipeline(verbose=args.verbose)
    result = pipeline.compile(source, filename)

    if not result.success:
        print(f"\n[COMPILE] Failed with {len(result.errors)} error(s):")
        for err in result.errors:
            print(f"  ✗ {err}")
        sys.exit(1)

    if args.emit_jir:
        print(f"\n{'='*60}")
        print("JIR OUTPUT:")
        print(f"{'='*60}")
        print(result.jir_text)

    if args.output:
        jir_path = args.output
        with open(jir_path, "w") as f:
            f.write(result.jir_json)
        print(f"\n[COMPILE] JIR written to: {jir_path}")

    print(f"\n[COMPILE] Success — investigation program ready for build.")


def cmd_build(args):
    """Handle: jocky build <file> --output <exe>"""
    filepath = args.file

    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r") as f:
        source = f.read()

    filename = os.path.basename(filepath)

    # Compile first
    pipeline = CompilerPipeline(verbose=True)
    result = pipeline.compile(source, filename)

    if not result.success:
        print(f"\n[BUILD] Compilation failed.")
        sys.exit(1)

    # Simulated build step — in production this would invoke the Forge
    output = args.output or "agent.bin"
    print(f"\n[BUILD]    Generating agent binary...", end="")

    # Create a placeholder build artifact with the JIR embedded
    import hashlib
    import secrets

    # Mutation seed — makes each build unique
    mutation_seed = secrets.token_hex(16)
    build_content = f"JOCKY_AGENT_v1\n{mutation_seed}\n{result.jir_json}"
    build_hash = hashlib.sha256(build_content.encode()).hexdigest()

    with open(output, "wb") as f:
        f.write(build_content.encode())

    print(f"              OK")
    print(f"[BUILD]    Output:     {output}")
    print(f"[BUILD]    SHA-256:    {build_hash}")
    print(f"[BUILD]    Mutation:   {mutation_seed[:16]}...")
    print(f"[BUILD]    Build complete.")


def cmd_forge(args):
    """Handle: jocky forge deploy <file> --targets <hosts>"""
    from .forge.builder import ForgeBuilder

    filepath = args.file
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r") as f:
        source = f.read()

    targets = [t.strip() for t in args.targets.split(",")]

    builder = ForgeBuilder()
    builder.deploy(source, os.path.basename(filepath), targets)


def cmd_dispatch(args):
    """Handle: jocky dispatch <file> --targets <hosts|ALL>"""
    # Placeholder — dispatch is multi-endpoint execution
    print(f"[DISPATCH] Dispatching to targets: {args.targets}")
    print(f"[DISPATCH] This feature requires the Spectre Agent runtime.")
    print(f"[DISPATCH] Use 'jocky forge deploy' to generate per-host builds first.")


def main():
    parser = argparse.ArgumentParser(
        prog="jocky",
        description="JOCKY — Forensic Investigation Framework",
    )
    parser.add_argument("--version", action="version", version="JOCKY 0.1.0 (FALCON)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── compile ──
    compile_parser = subparsers.add_parser("compile", help="Compile a .jky investigation program")
    compile_parser.add_argument("file", help="Path to .jky source file")
    compile_parser.add_argument("--verbose", "-v", action="store_true", help="Show compilation stages")
    compile_parser.add_argument("--emit-jir", action="store_true", help="Print JIR output")
    compile_parser.add_argument("--output", "-o", help="Write JIR JSON to file")

    # ── build ──
    build_parser = subparsers.add_parser("build", help="Compile and build agent binary")
    build_parser.add_argument("file", help="Path to .jky source file")
    build_parser.add_argument("--output", "-o", default="agent.bin", help="Output binary path")

    # ── forge deploy ──
    forge_parser = subparsers.add_parser("forge", help="Polymorphic build pipeline")
    forge_sub = forge_parser.add_subparsers(dest="forge_command")
    deploy_parser = forge_sub.add_parser("deploy", help="Deploy to multiple targets")
    deploy_parser.add_argument("file", help="Path to .jky source file")
    deploy_parser.add_argument("--targets", "-t", required=True, help="Comma-separated host list")

    # ── dispatch ──
    dispatch_parser = subparsers.add_parser("dispatch", help="Dispatch investigation to endpoints")
    dispatch_parser.add_argument("file", help="Path to .jky source file")
    dispatch_parser.add_argument("--targets", "-t", required=True, help="Target hosts or ALL")

    args = parser.parse_args()

    if args.command is None:
        print(BANNER)
        parser.print_help()
        return

    if args.command == "compile":
        cmd_compile(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "forge":
        cmd_forge(args)
    elif args.command == "dispatch":
        cmd_dispatch(args)


if __name__ == "__main__":
    main()
