#!/usr/bin/env python3
"""Test script for the UDP echo server.

Usage:
    python3 scripts/test_udp_echo.py [host] [port]

Defaults to localhost:9000. Sends a few test strings and verifies
the server echoes them back.
"""

import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
TIMEOUT = 3

TEST_STRINGS = [
    "hello",
    "openhost",
    "abc123!@#",
    "",
    "x" * 1000,
]


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    passed = 0
    failed = 0

    for msg in TEST_STRINGS:
        label = repr(msg) if len(msg) <= 40 else repr(msg[:40]) + "..."
        try:
            sock.sendto(msg.encode(), (HOST, PORT))
            data, _ = sock.recvfrom(4096)
            if data == msg.encode():
                print(f"  PASS: {label}")
                passed += 1
            else:
                print(f"  FAIL: {label} — got {data!r}")
                failed += 1
        except socket.timeout:
            print(f"  FAIL: {label} — timeout (server not responding)")
            failed += 1

    sock.close()

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    print(f"Testing UDP echo server at {HOST}:{PORT}\n")
    main()
