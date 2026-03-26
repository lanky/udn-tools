#!/usr/bin/env python3
"""Parse the chords-above format into UDN."""
import argparse
import re
import sys
from pathlib import Path

# generic chord pattern. Might also generate false positives
CHORD=re.compile(r"[A-G][adgijmnsu0-9#b+-\/\*A-G]*")

def parse_cmdline(argv: list[str] = sys.argv[1:]) -> argparse.Namespace:
    """Process commandline arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("source", type="Path", help="Path to chordsheet in UG format.")

    return parser.parse_args()

def chords_to_udn(source: Path):
    """Parse a UG-style chordsheet into UDN."""
    data = source.read_text().splitlines()
    # General approach:
    # read line-by-line, 
    # if empty, add to output
    # if a section header ([blah]), add to  output
    # if chords, pull next line
    # if next line also chords, brackets and add to  output
    # if not, insert chords into lyrics in same position (mind offsets)

    # TODO: add pychord verification of found patterns?


def main():
    """Import a chordsheet and parse it."""
    opts = parse_cmdline(sys.argv[1:])

if __name__ == "__main__":
    main()
