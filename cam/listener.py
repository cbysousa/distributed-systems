import socket
import struct


MULTICAST_GROUP = "239.0.0.1"
DISCOVERY_PORT = 9999
NAME = "cam"
CONTROLLABLE = "1"
SERVICE_PORT = 10001


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    sock.bind(("", DISCOVERY_PORT))

    membership = struct.pack(
        "4s4s",
        socket.inet_aton(MULTICAST_GROUP),
        socket.inet_aton("0.0.0.0"),
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)

    print(f"{NAME} listening on {MULTICAST_GROUP}:{DISCOVERY_PORT}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode("utf-8").strip()

        if message == "DISCOVER":
            response = f"{NAME}|{CONTROLLABLE}|{SERVICE_PORT}"
            sock.sendto(response.encode("utf-8"), addr)


if __name__ == "__main__":
    main()
