#!/usr/bin/env python3
# MIT License
# 
# Copyright (c) [year] [fullname]
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import re
from itertools import groupby, count
from pathlib import Path
from sortedcontainers import SortedDict, SortedSet
from time import strftime, gmtime
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

    regex = re.compile(r".*Host: (?P<ip>[0-9.]+) \(\)\s*"
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


def gen_axiom(parsed: OpenPortsHost, module: str, args: str) -> str:
    filename = strftime("%Y%m%d_%H%M%S_axiominput.txt", gmtime())
    with Path(filename).open("w") as f:
        for host in parsed.keys():
            f.write(host + '\n')

    all_tcp = SortedSet()
    all_udp = SortedSet()

    for _, ports_dict in parsed.items():
        all_tcp = all_tcp.union(ports_dict["tcp"])
        all_udp = all_udp.union(ports_dict["udp"])

    ports = ""

    if len(all_tcp) > 0:
        ports += "T:" + _make_ranges(all_tcp)
    if len(all_udp) > 0:
        if len(ports) > 0:
            ports += ","
        ports += "U:" + _make_ranges(all_udp)


    if args is None:
        args = "-A"
        if len(all_tcp) > 0:
            args += " -sS"
        if len(all_udp) > 0:
            args += " -sU"

    return f"axiom-scan {filename} -m {module} -p{ports} {args}"


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
        "--axiom",
        action="store_true",
        help="Create file and output command for axiom-scan"
        )
    parser.add_argument(
        "--axiom-module",
        help="Specify the module for axiom-scan (default: %(default)s)"
            " (implies --axiom)",
        default="nmap",
        )
    parser.add_argument(
        "--axiom-args",
        help="Specify args for axiom-scan (implies --axiom)",
        )
    parser.add_argument(
        "file",
        help="File to parse from",
        type=Path,
        )

    args = parser.parse_args()

    if args.axiom_module is not None or args.axiom_args is not None:
        args.axiom = True

    parsed = None

    if args.format == "masscan":
        parsed = parse_masscan(args.file)


    if not args.axiom:
        for cmd in gen_cli(parsed, args.nmap_cli):
            print(cmd)
    else:
        cmd = gen_axiom(parsed, args.axiom_module, args.axiom_args)
        print(cmd)


if __name__ == "__main__":
    main()
