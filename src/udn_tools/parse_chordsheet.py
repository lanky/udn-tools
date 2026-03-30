#!/usr/bin/env python3
"""Parse the chords-above format into UDN."""

import argparse
import re
import sys
from pathlib import Path

from loguru import logger
from pychord import Chord

logger.remove()

logger.add(Path("processing.log"), format="{level} | {message}")

# generic chord pattern. Might also generate false positives
chordpatt = r"[A-G][adgijmnsu0-9#b+-\/\*A-G]*"
CHORD = re.compile(rf"({chordpatt})")
# used to match whole lines for chords (only chords and whitespace)
CHORDLINE = re.compile(rf"(\s*({chordpatt})\s*)+")


def parse_cmdline(argv: list[str] = sys.argv[1:]) -> argparse.Namespace:
    """Process commandline arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        "source",
        type=Path,
        help="Path to chordsheet in UG format.",
    )

    return parser.parse_args()


def merge_chords(chords: str, lyrics: str) -> str:
    """Insert chords into the lyrics line."""
    pos = 0
    merged = []
    for crd in CHORD.finditer(chords):
        # fail if this is not a valid chord
        m = crd.group(1)
        logger.debug(f"processing chord '{m}'")
        try:
            c = Chord(m)
            logger.debug(f"Found valid chord {c.chord}")
        except ValueError:
            logger.error(f"Invalid chord match: {m}, skipping line.")
            return "\n".join([chords, lyrics])

        # extract lyrics up to chord position
        merged.append(lyrics[pos : crd.start()])
        # insert chord,  surrounded by ()
        merged.append(f"({crd.group()})")
        # move start position in lyrics line
        pos = crd.start()
    # finally, add the rest of the line (after the last chord)
    merged.append(lyrics[pos:])
    # join the results and return them
    return "".join(merged)

def is_chordline(line: str) -> bool:
    """Test if a matched line contains only (valid) chords and whitespace."""

    if CHORDLINE.match(line):
        # okay, we match the patterns, but are we actually chords?
        for crd in CHORD.finditer(line):
            try:
                _v = Chord(crd.group(1))
            except ValueError:
                logger.error(f"line contains invalid chord match {crd.group(1)}")
                return False
        return True
    else:
        return False


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
    parsed = []
    while len(data):
        # fetch the next line
        line = data.pop(0)
        logger.debug(f"Processing line '{line}'")

        if len(line.strip()) == 0:
            logger.debug("empty line")
            parsed.append(line)
        elif line.strip().startswith("["):
            # pass through empty lines or
            logger.debug(f"appending line: '{line}'")
            parsed.append(line.lower())
        elif is_chordline(line):
            # first, was this a valid chord match?
            # we need to inspect the next line
            try:
                nxt = data.pop(0)
                # surround chords with ()
                # if the next line is blank or a section heading...
                if len(nxt.strip()) == 0 or nxt.strip().startswith("["):
                    parsed.append(CHORD.sub(r"(\1)", line))
                    parsed.append(nxt)
                elif is_chordline(nxt):
                    parsed.append(CHORD.sub(r"(\1)", line))
                    parsed.append(CHORD.sub(r"(\1)", nxt))
                else:
                    # assume it's lyrics
                    parsed.append(merge_chords(line, nxt))
            except IndexError:
                # there is no next line
                parsed.append(CHORD.sub(r"(\1)", line))
        else:
            # don't know  what to do, let's include this line anyway
            parsed.append(line)
    return "\n".join(parsed)


def main():
    """Import a chordsheet and parse it."""
    opts = parse_cmdline(sys.argv[1:])

    if opts.source.exists():
        processed = chords_to_udn(opts.source)
        # print(processed)
        opts.source.with_suffix(".udn").write_text(processed)


if __name__ == "__main__":
    main()
