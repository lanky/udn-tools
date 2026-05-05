#!/usr/bin/env python3
"""Download and convert a songsheet from Ultimate Guitar."""

import argparse
import sys
from pathlib import Path

from bs4 import BeautifulSoup as bs
from loguru import logger

from udn_tools.parse_chordsheet import chords_to_udn
from udn_tools.ug_fetch import extract_tab, fetch_source, parse_meta

logger.remove()


def parse_cmdline(argv: list[str] = sys.argv[1:]) -> argparse.Namespace:
    """Process commandline arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        "source",
        help="URL to  Ultimate Guitar chordsheet.",
    )

    parser.add_argument(
        "-c",
        "--save-chords",
        action="store_true",
        help="save chordsheet before conversion.",
    )
    parser.add_argument(
        "-s",
        "--save-source",
        action="store_true",
        help="save source HTML (for debugging, mostly)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output filename. Auto-generated if not provided",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show debug log messages",
    )

    args = parser.parse_args(argv)

    if args.debug:
        args.loglevel = "DEBUG"
    else:
        args.loglevel = "INFO"

    return args


def main():
    opts = parse_cmdline(sys.argv[1:])

    logger.add(
        sys.stdout,
        level=opts.loglevel,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>ug_converter</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    logger.info(f"Fetching {opts.source}")

    soup = bs(fetch_source(opts.source), features="lxml")

    meta = parse_meta(soup)
    if meta:
        header = f"{meta['title']} - {meta['artist']}"
        logger.info(f"Parsed `{header}` from source")
    else:
        header = "Unknown Title - Unknown Artist"
        logger.warning("Unable to parse metadata")

    if opts.save_source:
        src_out = Path(f"{opts.source.split('/')[-1]}.html")
        src_out.write_text(soup.prettify())
        logger.debug(f"Wrote HTML to {src_out}")

    if opts.output:
        output = Path(opts.output)
    else:
        output = Path(header.lower().replace(" ", "_"))

    tab = extract_tab(soup, opts.save_chords)

    if tab:
        logger.info(f"Parsed chords from {opts.source}")

    udn = chords_to_udn(tab)
    if udn:
        logger.info(f"Saving UDN to {output.with_suffix('.udn')}")
        output.with_suffix(".udn").write_text(udn)


if __name__ == "__main__":
    main()
