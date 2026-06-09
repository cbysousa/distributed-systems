
import socket
import struct
import os
import client_pb2
import lamppost_pb2


GATEWAY_HOST = os.getenv("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "12000"))


def read_exact(sock, size):
    data = b""

    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("conexão encerrada pelo Gateway")
        data += chunk

    return data


def read_message(sock):
    header = read_exact(sock, 4)
    message_size = struct.unpack(">I", header)[0]
    return read_exact(sock, message_size)


def write_message(sock, payload):
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def send_request(request):
    with socket.create_connection((GATEWAY_HOST, GATEWAY_PORT), timeout=5) as sock:
        write_message(sock, request.SerializeToString())
        response_data = read_message(sock)

    response = client_pb2.ClientResponse()
    response.ParseFromString(response_data)
    return response


def list_sources():
    request = client_pb2.ClientRequest(
        list_sources=client_pb2.ListSourcesRequest()
    )

    response = send_request(request)

    sources = []

    if response.HasField("list_sources"):
        for source in response.list_sources.sources:
            sources.append({
                "name": source.name,
                "address": source.address,
                "ip": source.ip,
                "port": source.port,
                "controllable": source.controllable,
                "status": source.status,
                "last_seen_unix_ms": source.last_seen_unix_ms,
                "source_type": source.source_type,
            })

    return {
        "success": response.success,
        "message": response.message,
        "sources": sources,
    }


def list_readings(source_name="", metric=""):
    request = client_pb2.ClientRequest(
        list_readings=client_pb2.ListReadingsRequest()
    )

    response = send_request(request)

    readings = []

    if response.HasField("list_readings"):
        for reading in response.list_readings.readings:
            if source_name and reading.source_name != source_name:
                continue

            if metric and reading.metric != metric:
                continue

            readings.append({
                "source_name": reading.source_name,
                "source_type": reading.source_type,
                "metric": reading.metric,
                "value": reading.value,
                "unit": reading.unit,
                "timestamp_unix_ms": reading.timestamp_unix_ms,
            })

    readings.sort(key=lambda item: item["timestamp_unix_ms"])

    return {
        "success": response.success,
        "message": response.message,
        "readings": readings,
    }


def aggregate(source_name, metric, operation, window_seconds):
    operation_map = {
        "avg": client_pb2.AGGREGATE_OPERATION_AVG,
        "stddev": client_pb2.AGGREGATE_OPERATION_STDDEV,
        "min": client_pb2.AGGREGATE_OPERATION_MIN,
        "max": client_pb2.AGGREGATE_OPERATION_MAX,
    }

    request = client_pb2.ClientRequest(
        aggregate=client_pb2.AggregateRequest(
            source_name=source_name,
            metric=metric,
            operation=operation_map[operation],
            window_seconds=window_seconds,
        )
    )

    response = send_request(request)

    result = None

    if response.HasField("aggregate"):
        aggregate_response = response.aggregate
        result = {
            "source_name": aggregate_response.source_name,
            "metric": aggregate_response.metric,
            "operation": operation,
            "value": aggregate_response.value,
            "sample_count": aggregate_response.sample_count,
            "window_seconds": aggregate_response.window_seconds,
            "unit": aggregate_response.unit,
        }

    return {
        "success": response.success,
        "message": response.message,
        "aggregate": result,
    }


def send_lamppost_command(source_name, command):
    request = client_pb2.ClientRequest(
        send_command=client_pb2.SendCommandRequest(
            source_name=source_name,
            lamppost=command,
        )
    )

    response = send_request(request)

    result = None

    if response.HasField("send_command"):
        command_response = response.send_command
        result = {
            "success": command_response.success,
            "message": command_response.message,
            "source_status": command_response.source_status,
            "luminosity_percent": command_response.luminosity_percent,
            "light_on": command_response.light_on,
        }

    return {
        "success": response.success,
        "message": response.message,
        "command": result,
    }


def lamppost_turn_on(source_name):
    command = lamppost_pb2.LamppostCommand(
        turn_on=lamppost_pb2.LamppostTurnOnRequest()
    )
    return send_lamppost_command(source_name, command)


def lamppost_turn_off(source_name):
    command = lamppost_pb2.LamppostCommand(
        turn_off=lamppost_pb2.LamppostTurnOffRequest()
    )
    return send_lamppost_command(source_name, command)


def lamppost_get_state(source_name):
    command = lamppost_pb2.LamppostCommand(
        get_state=lamppost_pb2.LamppostGetStateRequest()
    )
    return send_lamppost_command(source_name, command)


def lamppost_set_luminosity(source_name, luminosity_percent):
    command = lamppost_pb2.LamppostCommand(
        set_luminosity=lamppost_pb2.LamppostSetLuminosityRequest(
            luminosity_percent=luminosity_percent
        )
    )
    return send_lamppost_command(source_name, command)


def lamppost_simulate_failure(source_name):
    command = lamppost_pb2.LamppostCommand(
        simulate_failure=lamppost_pb2.LamppostSimulateFailureRequest()
    )
    return send_lamppost_command(source_name, command)