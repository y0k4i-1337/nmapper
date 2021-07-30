#!/usr/bin/env python3

import argparse
import re
from pathlib import Path
from sortedcontainers import SortedSet
from typing import List, Mapping, TypeVar, TypedDict

PathT = TypeVar('PathT', Path, None)
ParsedCommands = List[str]
OpenPorts = Mapping[str, SortedSet]

class OpenPorts(TypedDict):
    tcp: SortedSet
    udp: SortedSet


class OpenPortsHost(TypedDict):
    host: str
    ports: OpenPorts


def parse_masscan(path: PathT, nmap_cli: str = None) -> ParsedCommands:
    if nmap_cli is None:
        nmap_cli = "nmap"
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    if not path.is_file():
        raise ValueError("path is not a valid file")

    regex = re.compile(r"^Host: (?P<ip>[0-9.]+) \(\)\t"
        r"Ports: (?P<port>[0-9]+)/open/"
        r"(?P<proto>tcp|udp)")

    with path.open() as f:
        for line in f:
            m = re.match(regex, line)
            if m:
                print(f"{m.group('ip')=} {m.group('port')=} {m.group('proto')=}")



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f",
        "--format",
        metavar="FORMAT",
        help="Input file format (default: %(default)s, choices: %(choices)s)",
        default="masscan",
        choices=["masscan"],
        )
    parser.add_argument(
        "--nmap-cli",
        help="Specify nmap command to use",
        )
    parser.add_argument(
        "file",
        help="File to parse from",
        type=Path,
        )

    args = parser.parse_args()

    if args.format == "masscan":
        parse_masscan(args.file, args.nmap_cli)

if __name__ == "__main__":
    main()
