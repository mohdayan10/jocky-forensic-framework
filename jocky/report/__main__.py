"""Entry point for: python3 -m jocky.report"""

import argparse
from ..demo import build_demo_evidence, build_demo_timeline, build_demo_graph
from ..common.evidence import InvestigationCase
from ..correlation.engine import CorrelationEngine
from ..blockchain.ledger import IntegrityLedger
from .generator import ReportGenerator, ReportConfig


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.report",
        description="JOCKY Report — Investigation report generation",
    )
    sub = parser.add_subparsers(dest="command")

    gen_p = sub.add_parser("generate", help="Generate investigation report")
    gen_p.add_argument("--case", required=True, help="Case ID")
    gen_p.add_argument("--format", default="json,pdf",
                       help="Comma-separated formats: json, pdf (default: json,pdf)")
    gen_p.add_argument("--output-dir", default="/tmp/jocky_reports",
                       help="Output directory")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    evidence = build_demo_evidence(args.case)
    timeline = build_demo_timeline()
    graph = build_demo_graph()

    case = InvestigationCase(
        case_id=args.case,
        investigator="SIH Team JOCKY",
        organization="NTRO Authorized",
        endpoints=["HOST-01 (Windows)", "HOST-02 (Ubuntu)", "HOST-03 (Windows)"],
        evidence=evidence,
        timeline=timeline,
        graph=graph,
    )

    # Generate findings
    engine = CorrelationEngine()
    case.findings = engine.correlate(evidence, args.case, "HOST-01")

    # Anchor to blockchain
    ledger = IntegrityLedger()
    ledger.anchor_batch(evidence, args.case)

    formats = [f.strip() for f in args.format.split(",")]
    config = ReportConfig(formats=formats, output_dir=args.output_dir)

    generator = ReportGenerator(ledger=ledger)
    generator.generate_verbose(case, config)


if __name__ == "__main__":
    main()
