"""Simple UDP echo server.

Receives datagrams on port 9000 and echoes each one back to the sender.
Uses only the stdlib.
"""

import socket

PORT = 9000


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    print(f"udp_echo: listening on :{PORT}", flush=True)

    while True:
        data, addr = sock.recvfrom(4096)
        print(f"udp_echo: {addr} -> {data!r}", flush=True)
        sock.sendto(data, addr)


if __name__ == "__main__":
    main()
