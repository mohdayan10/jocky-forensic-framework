#!/usr/bin/env python3
"""Django management script for JOCKY Command Console."""
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jocky.web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise ImportError("Django is required for the Command Console. Install it: pip install django")
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
