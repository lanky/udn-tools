#!/usr/bin/env python3

import argparse
import json
import re
import sys
from typing import List

import requests
from beautifulsoup4 import BeautifulSoup as bs

FORMATS = {
    "chords": 300,
    "bass": 400,
    "guitarpro": 500,
    "power_tab": 600,
    "uke": 800,
    "official": 900,
}
CRD = re.compile(r"(\[ch])(.*?)(\[/ch])")
TAB = re.compile(r"\[/?tab]")


def parse_cmdline(argv: List[str]) -> argparse.Namespace:
    """
    Process commandline arguments/options
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("title", help="string to search for, song title usualy")
    parser.add_argument("-a", "--artist", help="artist name")
    parser.add_argument(
        "-t",
        "--type",
        choices=["official", "tab", "pro_tab", "power_tab", "bass_tab", "uke"],
        help="result type",
    )

    parser.add_argument(
        "-l", "--list", action="store_true", default=False, help="list results"
    )

    opts = parser.parse_args(argv)

    return opts


def parse_tab(tablines: List[str]) -> List[str]:
    """
    parses the custom format used by UG into a more UDN-like one
    - removes [/?tab] markers
    - strips [ch]CHORD[/ch] wrappers
    - inserts chords into the appropriate positions on lyric lines
    """
    parsed = []
    # while we have unprocessed lines
    while len(tablines):
        # get the next line
        curline = tablines.pop(0)
        if curline.strip() == "":
            # preserve empty lines
            parsed.append(curline)
        elif CRD.search(curline) is not None:
            # this line contains chords
            try:
                # is the next line a non-chord (lyric) line?
                if CRD.search(tablines[0]) is None:
                    lyricline = list(tablines.pop(0))
                    for i, crd in enumerate(CRD.finditer(curline)):
                        # we shift left by multiples of the enclosing tags
                        # i.e. len([ch]) + len([/ch]) x (no. chords already seen - 1)
                        # the -1 reflects the fact that the lyric line gets one entry
                        # longer every time we insert a chord.
                        insert_pos = crd.start() - i * (len(crd[1]) + len(crd[3]) - 1)
                        lyricline.insert(insert_pos, f"({crd[2]})")
                    parsed.append("".join(lyricline))
                else:
                    # next line is chords as well
                    # do a global search and replace:
                    # this also removes leading pipe chars which are
                    # special in ukedown/markdown
                    parsed.append(CRD.sub(r"(\2)", curline).lstrip("|"))
            except IndexError:
                # there is no next line, replace any chords on this one and add it
                parsed.append(CRD.sub(r"(\2)", curline).lstrip("|"))
        else:
            parsed.append(curline)

    return parsed


def parse_ug(url: str) -> dict:
    """
    process the content of a UG page

    Args:
        url: URL to ultimate Guitar Page

    Returns:
        data: dict
    """
    # data_div = bs(response).find('div', {'class': 'js-store'})
    # metadata = data_div['data-content']
    # data['store']['page']['data']['tab_view']['wiki_tab']['content']
    response = requests.get(url)
    output = {}
    if response.ok:
        # track down the data
        soup = bs(response.content, features="lxml")
        blob = json.loads(soup.find("div", {"class": "js-store"})["data-content"])

        pagedata = blob["store"]["page"]["data"]

        # include artist and title for metadata
        output["artist"] = pagedata["tab"]["artist_name"]
        output["title"] = pagedata["tab"]["song_name"]
        # remove the [/?tab] delimiters, they just get in the way
        output["raw"] = TAB.sub("", pagedata["tab_view"]["wiki_tab"]["content"])
        output["parsed"] = parse_tab(output["raw"].splitlines())

        output["dump"] = pagedata

        # add in a few metadata fields which we can extract from the raw JSON
        output["meta"] = {
            "artist": pagedata["tab"].get("artist_name"),
            "title": pagedata["tab"].get("song_name"),
            "original_key": pagedata["tab"].get("tonality_name"),
            "source": pagedata["tab"].get("tab_url"),
            "transcriber": pagedata["tab"].get("username"),
        }

    return output


def main(opts):
    """
    Run a query against UG.
    """
    pass


if __name__ == "__main__":
    """
    Called when script is executed directly
    """
    opts = parse_cmdline(sys.argv[1:])

    main(opts)
