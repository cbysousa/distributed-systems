import socket
import struct
import threading
import time

import discovery_pb2
import lamppost_pb2
import readings_pb2


MULTICAST_GROUP = "239.0.0.1"
DISCOVERY_PORT = 9999
CONTROL_HOST = "0.0.0.0"
CONTROL_PORT = 10002
NAME = "lamppost"
SOURCE_TYPE = "lamppost"
STATUS_ACTIVE = "ACTIVE"
STATUS_OFFLINE = "OFFLINE"
READING_INTERVAL_SECONDS = 5
FAILURE_DURATION_SECONDS = 15

gateway_ip = None
gateway_readings_port = None


class LamppostState:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = True
        self.light_on = True
        self.luminosity_percent = 100.0
        self.energy_consumption_kwh = 0.0
        self.last_energy_update = time.time()
        self.failure_until = 0

    def status(self):
        return STATUS_OFFLINE if self.is_failed() else STATUS_ACTIVE

    def is_failed(self):
        return time.time() < self.failure_until

    def update_energy(self):
        now = time.time()
        elapsed_hours = (now - self.last_energy_update) / 3600
        self.last_energy_update = now

        if self.active and self.light_on:
            power_kw = 0.08 * (self.luminosity_percent / 100)
            self.energy_consumption_kwh += power_kw * elapsed_hours

    def turn_on(self):
        with self.lock:
            self.update_energy()
            self.active = True
            self.light_on = True
            if self.luminosity_percent == 0:
                self.luminosity_percent = 100.0
            return self.response(True, "lamppost light turned on")

    def turn_off(self):
        with self.lock:
            self.update_energy()
            self.active = True
            self.light_on = False
            self.luminosity_percent = 0.0
            return self.response(True, "lamppost light turned off")

    def get_state(self):
        with self.lock:
            self.update_energy()
            return self.response(True, "lamppost state returned")

    def simulate_failure(self):
        with self.lock:
            self.update_energy()
            self.failure_until = time.time() + FAILURE_DURATION_SECONDS
            self.light_on = False
            self.luminosity_percent = 0.0
            return self.response(True, f"lamppost failure simulated for {FAILURE_DURATION_SECONDS} seconds")

    def set_luminosity(self, luminosity_percent):
        with self.lock:
            self.update_energy()
            self.luminosity_percent = max(0.0, min(100.0, luminosity_percent))
            self.active = True
            self.light_on = self.luminosity_percent > 0
            return self.response(True, "lamppost luminosity updated")

    def reading_packet(self):
        with self.lock:
            if self.is_failed():
                return None

            self.update_energy()

            packet = readings_pb2.ReadingPacket(
                source_name=NAME,
                timestamp_unix_ms=int(time.time() * 1000),
                lamppost=lamppost_pb2.LamppostReading(
                    luminosity_percent=self.luminosity_percent,
                    energy_consumption_kwh=self.energy_consumption_kwh,
                    light_on=self.light_on,
                ),
            )

            return packet, self.luminosity_percent, self.energy_consumption_kwh, self.light_on

    def response(self, success, message):
        return lamppost_pb2.LamppostResponse(
            success=success,
            message=message,
            active=self.active,
            status=self.status(),
            luminosity_percent=self.luminosity_percent,
            energy_consumption_kwh=self.energy_consumption_kwh,
            light_on=self.light_on,
        )


lamppost_state = LamppostState()


def read_exact(conn, size):
    data = b""
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            raise ConnectionError("connection closed")
        data += chunk
    return data


def read_message(conn):
    header = read_exact(conn, 4)
    message_size = struct.unpack(">I", header)[0]
    return read_exact(conn, message_size)


def write_message(conn, payload):
    conn.sendall(struct.pack(">I", len(payload)) + payload)


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

        with lamppost_state.lock:
            if lamppost_state.is_failed():
                continue

            response = discovery_pb2.DiscoveryResponse(
                source_name=NAME,
                source_type=SOURCE_TYPE,
                control_port=CONTROL_PORT,
                controllable=True,
                status=lamppost_state.status(),
            )

        sock.sendto(response.SerializeToString(), addr)
        print(f"[{NAME}] discovered gateway {request.gateway_id} at {gateway_ip}:{gateway_readings_port}")


def send_readings():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if gateway_ip and gateway_readings_port:
            reading = lamppost_state.reading_packet()
            if reading:
                packet, luminosity_percent, energy_consumption_kwh, light_on = reading

                try:
                    sock.sendto(packet.SerializeToString(), (gateway_ip, gateway_readings_port))
                    print(
                        f"[{NAME}] sent luminosity={luminosity_percent}% "
                        f"energy={energy_consumption_kwh:.4f}kWh light_on={light_on}"
                    )
                except Exception as error:
                    print(f"[{NAME}] failed to send reading: {error}")

        time.sleep(READING_INTERVAL_SECONDS)


def handle_command(command):
    command_type = command.WhichOneof("command")

    if command_type == "turn_on":
        return lamppost_state.turn_on()
    if command_type == "turn_off":
        return lamppost_state.turn_off()
    if command_type == "get_state":
        return lamppost_state.get_state()
    if command_type == "simulate_failure":
        return lamppost_state.simulate_failure()
    if command_type == "set_luminosity":
        return lamppost_state.set_luminosity(command.set_luminosity.luminosity_percent)

    return lamppost_pb2.LamppostResponse(
        success=False,
        message="unknown lamppost command",
        active=lamppost_state.active,
        status=lamppost_state.status(),
        luminosity_percent=lamppost_state.luminosity_percent,
        energy_consumption_kwh=lamppost_state.energy_consumption_kwh,
        light_on=lamppost_state.light_on,
    )


def handle_client(conn, addr):
    with conn:
        try:
            with lamppost_state.lock:
                if lamppost_state.is_failed():
                    return

            data = read_message(conn)
            command = lamppost_pb2.LamppostCommand()
            command.ParseFromString(data)

            response = handle_command(command)
            write_message(conn, response.SerializeToString())
            print(f"[{NAME}] command handled from {addr[0]}: {command.WhichOneof('command')}")
        except Exception as error:
            print(f"[{NAME}] command error from {addr[0]}: {error}")


def start_control_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((CONTROL_HOST, CONTROL_PORT))
    server.listen()

    print(f"[{NAME}] control TCP server listening on {CONTROL_HOST}:{CONTROL_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


def main():
    threading.Thread(target=listen_multicast, daemon=True).start()
    threading.Thread(target=send_readings, daemon=True).start()
    start_control_server()


if __name__ == "__main__":
    main()
