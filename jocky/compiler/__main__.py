"""Entry point for: python3 -m jocky.compiler"""

import argparse
import os
import sys

from .pipeline import CompilerPipeline


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.compiler",
        description="JOCKY Compiler — Compile .jky investigation programs",
    )
    parser.add_argument("file", help="Path to .jky source file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show compilation stages")
    parser.add_argument("--emit-jir", action="store_true", help="Print JIR output")
    parser.add_argument("--output", "-o", help="Write JIR JSON to file")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)

    with open(args.file) as f:
        source = f.read()

    filename = os.path.basename(args.file)
    pipeline = CompilerPipeline(verbose=args.verbose)
    result = pipeline.compile(source, filename)

    if not result.success:
        print(f"\n[COMPILE] Failed with {len(result.errors)} error(s):")
        for err in result.errors:
            print(f"  ✗ {err}")
        sys.exit(1)

    if args.emit_jir and result.jir_text:
        print(f"\n{'='*60}")
        print("JIR OUTPUT:")
        print(f"{'='*60}")
        print(result.jir_text)

    if args.output and result.jir_json:
        with open(args.output, "w") as f:
            f.write(result.jir_json)
        print(f"\n[COMPILE] JIR written to: {args.output}")

    print(f"\n[COMPILE] Success — investigation program ready for build.")


if __name__ == "__main__":
    main()
