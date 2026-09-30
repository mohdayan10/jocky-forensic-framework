"""Entry point for: python3 -m jocky.correlate"""

import argparse
from ..demo import build_demo_evidence
from ..correlation.engine import CorrelationEngine


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.correlate",
        description="JOCKY Correlation Engine — Multi-signal finding generation",
    )
    parser.add_argument("--case", required=True, help="Case ID")
    parser.add_argument("--host", default="HOST-01", help="Host to correlate (default: HOST-01)")

    args = parser.parse_args()

    evidence = build_demo_evidence(args.case)
    engine = CorrelationEngine()
    engine.correlate_verbose(evidence, case_id=args.case, host=args.host)


if __name__ == "__main__":
    main()
