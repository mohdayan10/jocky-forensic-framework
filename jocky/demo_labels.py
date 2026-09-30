"""Demo output labeling — every line is tagged as LIVE PIPELINE or SIMULATED AGENT.

Color legend:
  GREEN  [LIVE PIPELINE]       — output produced by real pipeline code
  YELLOW [SIMULATED AGENT]     — fixture data representing agent collection
  RED    [DEMO NOTE]           — explanatory annotation for evaluators
"""

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def live(msg: str):
    """Output from real pipeline code executing at demo runtime."""
    print(f"{GREEN}[LIVE PIPELINE]{RESET}  {msg}")


def simulated(msg: str):
    """Output from fixture data representing real agent collection."""
    print(f"{YELLOW}[SIMULATED AGENT]{RESET} {msg}")


def note(msg: str):
    """Explanatory annotation — not pipeline output."""
    print(f"{RED}[DEMO NOTE]{RESET}       {msg}")
