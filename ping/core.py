from __future__ import annotations

from ping.cmd import cmd_ping
from ping.tcp import tcp_ping
from ping.udp import udp_ping
from ping.icmp import icmp_ping


def sweep(host):
    # print(cmd_ping(host))
    print(icmp_ping(host))
    print(tcp_ping(host))
    print(udp_ping(host))


def main():
    sweep("news.ycombinator.com")


if __name__ == "__main__":
    main()
