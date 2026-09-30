"""Entry point for: python3 -m jocky.integrity"""

import argparse
from ..demo import build_demo_evidence
from ..blockchain.ledger import IntegrityLedger
from ..common.evidence import InvestigationCase


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.integrity",
        description="JOCKY Integrity — Blockchain evidence verification",
    )
    sub = parser.add_subparsers(dest="command")

    verify_p = sub.add_parser("verify", help="Verify evidence against blockchain ledger")
    verify_p.add_argument("--evidence-id", required=True, help="Evidence ID to verify")
    verify_p.add_argument("--case", required=True, help="Case ID")
    verify_p.add_argument("--tamper", action="store_true",
                          help="Simulate tamper before verification")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    evidence_list = build_demo_evidence(args.case)
    ledger = IntegrityLedger()
    ledger.anchor_batch(evidence_list, args.case)

    case = InvestigationCase(
        case_id=args.case, evidence=evidence_list,
    )

    ev = case.get_evidence(args.evidence_id)
    if ev is None:
        print(f"[ERROR] Evidence ID {args.evidence_id} not found in case {args.case}")
        return

    if args.tamper:
        ev.data["tampered_by_demo"] = True

    ledger.verify_verbose(ev)

    if args.tamper:
        del ev.data["tampered_by_demo"]


if __name__ == "__main__":
    main()
