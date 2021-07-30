#!/usr/bin/env python3

import argparse
import re
from itertools import groupby, count
from pathlib import Path
from sortedcontainers import SortedDict, SortedSet
from typing import Iterable, List, Mapping, TypeVar, TypedDict

PathT = TypeVar('PathT', Path, None)
SortedSetT = TypeVar('SortedSet', SortedSet, None)
ParsedCommands = List[str]
OpenPorts = Mapping[str, SortedSet]

class OpenPorts(TypedDict):
    tcp: SortedSet
    udp: SortedSet


class OpenPortsHost(TypedDict):
    host: str
    ports: OpenPorts


def parse_masscan(path: PathT) -> OpenPortsHost:
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
    if not path.is_file():
        raise ValueError("path is not a valid file")

    regex = re.compile(r"^Host: (?P<ip>[0-9.]+) \(\)\t"
        r"Ports: (?P<port>[0-9]+)/open/"
        r"(?P<proto>tcp|udp)")

    result = SortedDict()

    with path.open() as f:
        for line in f:
            m = re.match(regex, line)
            if m:
                ip, port, proto = m.groups()
                #print(f"{ip=} {port=} {proto=}")
                if ip not in result:
                    result[ip] = {
                            "tcp": SortedSet(),
                            "udp": SortedSet(),
                            }
                if proto == "tcp" or proto == "udp":
                    result[ip][proto].add(int(port))

    return result


def gen_cli(parsed: OpenPortsHost, nmap_cli: str=None) -> List[str]:
    default_cli = "nmap -A"
    if nmap_cli is None:
        nmap_cli = default_cli

    commands = []
    for host, ports_dict in parsed.items():
        args = ""
        ports = ""
        if len(ports_dict["tcp"]) > 0:
            if nmap_cli == default_cli:
                args = "-sS"
            ports = "T:" + _make_ranges(ports_dict["tcp"])
        if len(ports_dict["udp"]) > 0:
            if nmap_cli == default_cli:
                if len(args) > 0:
                    args += " "
                args += "-sU"
            if len(ports) > 0:
                ports += ","
            ports += "U:" + _make_ranges(ports_dict["udp"])
        if len(args) == 0:
            cmd = f"{nmap_cli} -p{ports} {host}"
        else:
            cmd = f"{nmap_cli} {args} -p{ports} {host}"
        commands.append(cmd)
    return commands


def _as_range(iterable: Iterable) -> str:
    l = list(iterable)
    if len(l) > 1:
        return f"{l[0]}-{l[-1]}"
    else:
        return f"{l[0]}"


def _make_ranges(ports: SortedSetT) -> str:
    return ','.join(_as_range(g) for _, g in groupby(list(ports),
        key=lambda n, c=count(): n-next(c)))


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

    parsed = None

    if args.format == "masscan":
        parsed = parse_masscan(args.file)


    for cmd in gen_cli(parsed, args.nmap_cli):
        print(cmd)


if __name__ == "__main__":
    main()
