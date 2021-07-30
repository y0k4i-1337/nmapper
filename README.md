# nmapper

Parse output from other port scanners into nmap command

## Description

This is a simple Python script that takes an output from a port scanner and
generate new nmap commands for detailed scans.

## Dependencies

This program was tested with Python 3.8.5. It probably works with older and earlier versions as well. There is no external dependencies.

## Usage

```
➜ ./nmapper.py -h

usage: nmapper.py [-h] [-f FORMAT] [--nmap-cli NMAP_CLI] file

positional arguments:
  file                  File to parse from

optional arguments:
  -h, --help            show this help message and exit
  -f FORMAT, --format FORMAT
                        Input file format (default: masscan, choices: masscan)
  --nmap-cli NMAP_CLI   Specify nmap command to use
```

## Supported inputs

Currently it only works with `masscan` grepable output.

## Examples

If you don't pass `--nmap-cli` option, the script will define nmap arguments as needed.

```
➜ ./nmapper.py sample/masscan.out
nmap -A -sS -pT:80,443 10.0.0.1
nmap -A -sS -pT:1984,10050 10.0.0.10
nmap -A -sS -pT:80,443,8008,8080,8443,9440-9443 172.16.20.20
nmap -A -sS -pT:80,443,8008,8080,8443,9440-9443 172.16.20.29
nmap -A -sS -pT:80,443 192.168.0.5
nmap -A -sS -pT:22,80,111,443,1984,9999,25060-25062,43319 192.168.0.7
```

Or you can define your own command:

```
➜ ./nmapper.py --nmap-cli "nmap -sT -A -T4" sample/masscan.out
nmap -sT -A -T4 -pT:80,443 10.0.0.1
nmap -sT -A -T4 -pT:1984,10050 10.0.0.10
nmap -sT -A -T4 -pT:80,443,8008,8080,8443,9440-9443 172.16.20.20
nmap -sT -A -T4 -pT:80,443,8008,8080,8443,9440-9443 172.16.20.29
nmap -sT -A -T4 -pT:80,443 192.168.0.5
nmap -sT -A -T4 -pT:22,80,111,443,1984,9999,25060-25062,43319 192.168.0.7
```

## License

This project is licensed under MIT License. See [LICENSE](LICENSE) for more details.
