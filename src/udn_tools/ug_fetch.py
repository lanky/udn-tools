#!/usr/bin/env python3
"""Fetch and parse a songsheet from ultimate guitar."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import jmespath
from bs4 import BeautifulSoup as bs
from selenium import webdriver

# naive pattern matching for chords
CHORD = re.compile(r"[A-G][adgijmnsu0-9#b+-\/\*A-G]*")


def parse_cmdline(argv: list[str] = sys.argv[1:]) -> argparse.Namespace:
    """Process commandline arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("source", help="URL to  Ultimate Guitar chordsheet.")
    parser.add_argument(
        "-s",
        "--save-source",
        action="store_true",
        default=False,
        help="Save the HTML source (for debugging)",
    )

    return parser.parse_args()


def fetch_source(url: str) -> str:
    """Fetch the page source from UG via selenium."""
    browser_opts = webdriver.FirefoxOptions()
    browser_opts.add_argument("--headless")

    browser = webdriver.Firefox(options=browser_opts)

    browser.get(url)

    return browser.page_source


def extract_tab(html: str, save: bool = False) -> str | None:
    """Parse the html to extract the tab/chords."""
    soup = bs(html, features="lxml")
    content = soup.find("pre", {"class": "k_vI3 KLhHx fGc1h"})

    meta = parse_meta(soup)

    print(meta)

    if content is not None:
        if footer := content.find("div", {"class": "d8c-l"}):
            footer.decompose()

        lines = content.text.splitlines()

        # header = "Unknown Title - Unknown Artist"
        if meta:
            header = f"{meta['title']} - {meta['artist']}"
        else:
            header = "Unknown Title - Unknown Artist"

        lines.insert(0, header)
        print(lines)

        dest = Path(header.lower().replace(" ", "_")).with_suffix(".crd")

        dest.write_text("\n".join(lines))
        return content.text
    return content


def parse_meta(soup: bs) -> dict:
    """Parse out metadata blobs."""
    # metadata is a JSONish blob stored as a script
    meta = soup.find("script", {"type": "application/ld+json"})
    if meta:
        metadata = json.loads(meta.text.replace("@", ""))
        return jmespath.search(
            """
        {
        title: name,
        artist: byArtist.name,
        url: url
        }
        """,
            metadata,
        )
    else:
        return {}


def main():
    """Run all the things."""
    opts = parse_cmdline(sys.argv[1:])

    print(f"Fetching source from {opts.source}")

    src = fetch_source(opts.source)

    if opts.save_source:
        Path(f"{opts.source.split('/')[-1]}.html").write_text(src)

    print("Attempting to parse sources")

    extract_tab(src)


if __name__ == "__main__":
    main()
