import random
import socket
import struct
import threading
import time

import discovery_pb2
import readings_pb2
import traffic_pb2


MULTICAST_GROUP = "239.0.0.1"
DISCOVERY_PORT = 9999

SOURCE_NAME = "traffic_sensor"
SOURCE_TYPE = "traffic"
STATUS = "ACTIVE"

gateway_ip = None
gateway_readings_port = 11000


def listen_discovery():
    global gateway_ip
    global gateway_readings_port

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

    print(f"[{SOURCE_NAME}] aguardando descoberta em {MULTICAST_GROUP}:{DISCOVERY_PORT}")

    while True:
        data, addr = sock.recvfrom(4096)

        request = discovery_pb2.DiscoveryRequest()

        try:
            request.ParseFromString(data)
        except Exception:
            continue

        gateway_ip = addr[0]

        if request.readings_port > 0:
            gateway_readings_port = request.readings_port

        response = discovery_pb2.DiscoveryResponse(
            source_name=SOURCE_NAME,
            source_type=SOURCE_TYPE,
            ip="",
            control_port=0,
            controllable=False,
            status=STATUS,
        )

        sock.sendto(response.SerializeToString(), addr)

        print(f"[{SOURCE_NAME}] Gateway encontrado em {gateway_ip}:{gateway_readings_port}")


def send_readings():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if gateway_ip is None:
            time.sleep(1)
            continue

        vehicles = random.randint(5, 80)

        traffic = traffic_pb2.TrafficReading(
            vehicles_per_minute=float(vehicles)
        )

        packet = readings_pb2.ReadingPacket(
            source_name=SOURCE_NAME,
            timestamp_unix_ms=int(time.time() * 1000),
            traffic=traffic,
        )

        sock.sendto(
            packet.SerializeToString(),
            (gateway_ip, gateway_readings_port),
        )

        print(f"[{SOURCE_NAME}] enviado: {vehicles} veículos/min")

        time.sleep(5)


def main():
    threading.Thread(target=listen_discovery, daemon=True).start()
    send_readings()


if __name__ == "__main__":
    main()