import random
import socket
import struct
import threading
import time

import air_quality_pb2
import discovery_pb2
import readings_pb2


MULTICAST_GROUP = "239.0.0.1"
DISCOVERY_PORT = 9999
NAME = "air-quality-sensor"
SOURCE_TYPE = "air_quality"
STATUS_ACTIVE = "ACTIVE"

gateway_ip = None
gateway_readings_port = None


def listen_multicast():
    global gateway_ip, gateway_readings_port

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

    print(f"[{NAME}] listening for discovery on {MULTICAST_GROUP}:{DISCOVERY_PORT}")

    while True:
        data, addr = sock.recvfrom(4096)
        request = discovery_pb2.DiscoveryRequest()

        try:
            request.ParseFromString(data)
        except Exception:
            continue

        gateway_ip = request.gateway_ip or addr[0]
        gateway_readings_port = request.readings_port

        response = discovery_pb2.DiscoveryResponse(
            source_name=NAME,
            source_type=SOURCE_TYPE,
            control_port=0,
            controllable=False,
            status=STATUS_ACTIVE,
        )

        sock.sendto(response.SerializeToString(), addr)
        print(
            f"[{NAME}] discovered gateway {request.gateway_id} "
            f"at {gateway_ip}:{gateway_readings_port}"
        )


def build_reading_packet():
    co2_ppm = round(random.uniform(350.0, 1200.0), 1)
    particulate_matter = round(random.uniform(5.0, 80.0), 1)
    air_quality_index = round(random.uniform(0.0, 200.0), 1)

    packet = readings_pb2.ReadingPacket(
        source_name=NAME,
        timestamp_unix_ms=int(time.time() * 1000),
        air_quality=air_quality_pb2.AirQualityReading(
            co2_ppm=co2_ppm,
            particulate_matter_ug_m3=particulate_matter,
            air_quality_index=air_quality_index,
        ),
    )

    return packet, co2_ppm, particulate_matter, air_quality_index


def send_continuous_data():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if gateway_ip and gateway_readings_port:
            packet, co2_ppm, particulate_matter, air_quality_index = build_reading_packet()

            try:
                sock.sendto(
                    packet.SerializeToString(),
                    (gateway_ip, gateway_readings_port),
                )
                print(
                    f"[{NAME}] sent co2={co2_ppm}ppm "
                    f"pm={particulate_matter}ug/m3 aqi={air_quality_index}"
                )
            except Exception as error:
                print(f"[{NAME}] failed to send reading: {error}")

        time.sleep(5)


def main():
    threading.Thread(target=listen_multicast, daemon=True).start()
    send_continuous_data()


if __name__ == "__main__":
    main()
