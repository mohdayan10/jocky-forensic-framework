"""Entry point for: python3 -m jocky.query"""

import argparse
import re
from ..console.dispatch import CommandConsole


def main():
    parser = argparse.ArgumentParser(
        prog="jocky.query",
        description="JOCKY Query — Cross-host evidence querying",
    )
    parser.add_argument("query", help='Query string, e.g. "find file WHERE hash == \'abc...\' ACROSS ALL hosts"')

    args = parser.parse_args()

    # Extract hash from query
    hash_match = re.search(r"hash\s*==\s*['\"]([a-fA-F0-9]+)['\"]", args.query)
    query_hash = hash_match.group(1) if hash_match else "7b4c3f2a819de4f5c6a7b8c9d0e1f2a3"

    # Extract hosts
    if "ALL" in args.query.upper():
        hosts = ["HOST-01", "HOST-02", "HOST-03"]
    else:
        host_matches = re.findall(r"HOST-\d+", args.query)
        hosts = host_matches if host_matches else ["HOST-01", "HOST-02", "HOST-03"]

    console = CommandConsole()
    console.cross_host_query_verbose(query_hash, hosts)


if __name__ == "__main__":
    main()
