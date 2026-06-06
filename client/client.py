import socket
import struct
from datetime import datetime

import client_pb2
import lamppost_pb2


GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 12000

METRICS_BY_SOURCE_TYPE = {
    "weather": [
        "temperature_celsius",
        "humidity_percent",
    ],
    "air_quality": [
        "co2_ppm",
        "particulate_matter_ug_m3",
        "air_quality_index",
    ],
    "lamppost": [
        "luminosity_percent",
        "energy_consumption_kwh",
    ],
}


def read_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("conexao encerrada pelo Gateway")
        data += chunk
    return data


def read_message(sock):
    header = read_exact(sock, 4)
    message_size = struct.unpack(">I", header)[0]
    return read_exact(sock, message_size)


def write_message(sock, payload):
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def send_request(request):
    try:
        with socket.create_connection((GATEWAY_HOST, GATEWAY_PORT), timeout=5) as sock:
            write_message(sock, request.SerializeToString())
            response_data = read_message(sock)
    except OSError as error:
        print(f"Erro ao conectar no Gateway: {error}")
        return None
    except ConnectionError as error:
        print(f"Erro de conexao: {error}")
        return None

    response = client_pb2.ClientResponse()
    try:
        response.ParseFromString(response_data)
    except Exception as error:
        print(f"Resposta invalida do Gateway: {error}")
        return None

    return response


def request_list_sources():
    return client_pb2.ClientRequest(
        list_sources=client_pb2.ListSourcesRequest(),
    )


def request_list_readings():
    return client_pb2.ClientRequest(
        list_readings=client_pb2.ListReadingsRequest(),
    )


def request_lamppost_command(source_name, command):
    return client_pb2.ClientRequest(
        send_command=client_pb2.SendCommandRequest(
            source_name=source_name,
            lamppost=command,
        ),
    )


def request_aggregate(source_name, metric, operation, window_seconds):
    return client_pb2.ClientRequest(
        aggregate=client_pb2.AggregateRequest(
            source_name=source_name,
            metric=metric,
            operation=operation,
            window_seconds=window_seconds,
        ),
    )


def print_sources(response):
    if not response or not response.HasField("list_sources"):
        print_gateway_message(response)
        return

    sources = response.list_sources.sources
    if not sources:
        print("Nenhuma fonte de dados encontrada.")
        return

    print("\nFontes de dados:")
    print("-" * 96)
    print(f"{'Nome':<24} {'Tipo':<16} {'Status':<10} {'Controlavel':<12} {'Endereco':<22} Ultimo Visto")
    print("-" * 96)

    for source in sources:
        last_seen = format_timestamp(source.last_seen_unix_ms)
        controllable = "sim" if source.controllable else "nao"
        address = source.address or "-"
        print(
            f"{source.name:<24} {source.source_type:<16} {source.status:<10} "
            f"{controllable:<12} {address:<22} {last_seen}"
        )


def print_readings(response):
    if not response or not response.HasField("list_readings"):
        print_gateway_message(response)
        return

    readings = response.list_readings.readings
    if not readings:
        print("Nenhuma leitura encontrada.")
        return

    print("\nLeituras:")
    print("-" * 112)
    print(f"{'Fonte':<24} {'Tipo':<14} {'Metrica':<28} {'Valor':<12} {'Unidade':<10} Timestamp")
    print("-" * 112)

    for reading in readings:
        timestamp = format_timestamp(reading.timestamp_unix_ms)
        print(
            f"{reading.source_name:<24} {reading.source_type:<14} {reading.metric:<28} "
            f"{reading.value:<12.2f} {reading.unit:<10} {timestamp}"
        )


def print_command_response(response):
    if not response or not response.HasField("send_command"):
        print_gateway_message(response)
        return

    command = response.send_command
    status = command.source_status or "-"
    result = "sucesso" if command.success else "falha"

    print(f"\nResultado: {result}")
    print(f"Mensagem: {command.message}")
    print(f"Status da fonte: {status}")
    if command.success:
        light_state = "ligada" if command.light_on else "desligada"
        print(f"Luminosidade: {command.luminosity_percent:.2f}%")
        print(f"Luz: {light_state}")


def print_aggregate_response(response):
    if not response or not response.HasField("aggregate"):
        print_gateway_message(response)
        return

    aggregate = response.aggregate
    window = "todas as leituras" if aggregate.window_seconds <= 0 else f"ultimos {aggregate.window_seconds}s"

    print("\nResultado da consulta:")
    print(f"Fonte: {aggregate.source_name}")
    print(f"Metrica: {aggregate.metric}")
    print(f"Operacao: {aggregate_operation_name(aggregate.operation)}")
    print(f"Valor: {aggregate.value:.4f}")
    print(f"Unidade: {aggregate.unit or '-'}")
    print(f"Amostras: {aggregate.sample_count}")
    print(f"Janela: {window}")


def print_gateway_message(response):
    if response:
        print(f"Mensagem do Gateway: {response.message}")


def format_timestamp(timestamp_unix_ms):
    if timestamp_unix_ms <= 0:
        return "-"

    return datetime.fromtimestamp(timestamp_unix_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def list_sources():
    response = send_request(request_list_sources())
    print_sources(response)


def list_readings():
    response = send_request(request_list_readings())
    print_readings(response)


def aggregate_query():
    source = select_source()
    if not source:
        return

    metric = select_metric(source)
    if not metric:
        return

    operation = read_aggregate_operation()
    if operation is None:
        return

    window_seconds = read_window_seconds()
    if window_seconds is None:
        return

    response = send_request(request_aggregate(source.name, metric, operation, window_seconds))
    print_aggregate_response(response)


def get_sources():
    response = send_request(request_list_sources())
    if not response or not response.HasField("list_sources"):
        print_gateway_message(response)
        return []

    return list(response.list_sources.sources)


def select_source():
    sources = get_sources()
    if not sources:
        print("Nenhuma fonte de dados encontrada.")
        return None

    print("\nFontes de dados:")
    for index, source in enumerate(sources, start=1):
        print(f"{index}. {source.name} | tipo={source.source_type} | status={source.status}")
    print("0. Voltar")

    while True:
        option = input("Escolha uma fonte: ").strip()
        if option == "0":
            return None

        try:
            source_index = int(option)
        except ValueError:
            print("Opcao invalida.")
            continue

        if 1 <= source_index <= len(sources):
            return sources[source_index - 1]

        print("Opcao invalida.")


def select_metric(source):
    metrics = METRICS_BY_SOURCE_TYPE.get(source.source_type, [])
    if not metrics:
        print(f"Nenhuma metrica de consulta configurada para o tipo {source.source_type}.")
        return None

    print(f"\nMetricas disponiveis para {source.name}:")
    for index, metric in enumerate(metrics, start=1):
        print(f"{index}. {metric}")
    print("0. Voltar")

    while True:
        option = input("Escolha uma metrica: ").strip()
        if option == "0":
            return None

        try:
            metric_index = int(option)
        except ValueError:
            print("Opcao invalida.")
            continue

        if 1 <= metric_index <= len(metrics):
            return metrics[metric_index - 1]

        print("Opcao invalida.")


def get_controllable_sources():
    return [source for source in get_sources() if source.controllable]


def select_controllable_source():
    sources = get_controllable_sources()
    if not sources:
        print("Nenhuma fonte controlavel encontrada.")
        return None

    print("\nFontes controlaveis:")
    for index, source in enumerate(sources, start=1):
        print(f"{index}. {source.name} | tipo={source.source_type} | status={source.status}")
    print("0. Voltar")

    while True:
        option = input("Escolha uma fonte: ").strip()
        if option == "0":
            return None

        try:
            source_index = int(option)
        except ValueError:
            print("Opcao invalida.")
            continue

        if 1 <= source_index <= len(sources):
            return sources[source_index - 1]

        print("Opcao invalida.")


def adjust_controllable_source():
    source = select_controllable_source()
    if not source:
        return

    while True:
        print(f"\n=== Ajustar fonte controlavel: {source.name} ===")
        print("1. Ligar luz da fonte")
        print("2. Desligar luz da fonte")
        print("3. Consultar estado")
        print("4. Ajustar luminosidade")
        print("0. Voltar")

        option = input("Escolha uma opcao: ").strip()

        if option == "1":
            command = lamppost_pb2.LamppostCommand(
                turn_on=lamppost_pb2.LamppostTurnOnRequest(),
            )
        elif option == "2":
            command = lamppost_pb2.LamppostCommand(
                turn_off=lamppost_pb2.LamppostTurnOffRequest(),
            )
        elif option == "3":
            command = lamppost_pb2.LamppostCommand(
                get_state=lamppost_pb2.LamppostGetStateRequest(),
            )
        elif option == "4":
            luminosity = read_luminosity()
            if luminosity is None:
                continue
            command = lamppost_pb2.LamppostCommand(
                set_luminosity=lamppost_pb2.LamppostSetLuminosityRequest(
                    luminosity_percent=luminosity,
                ),
            )
        elif option == "0":
            return
        else:
            print("Opcao invalida.")
            continue

        response = send_request(request_lamppost_command(source.name, command))
        print_command_response(response)


def simulate_failure():
    source = select_controllable_source()
    if not source:
        return

    command = lamppost_pb2.LamppostCommand(
        simulate_failure=lamppost_pb2.LamppostSimulateFailureRequest(),
    )
    response = send_request(request_lamppost_command(source.name, command))
    print_command_response(response)


def read_luminosity():
    value = input("Luminosidade de 0 a 100: ").strip()
    try:
        luminosity = float(value)
    except ValueError:
        print("Valor invalido.")
        return None

    if luminosity < 0 or luminosity > 100:
        print("A luminosidade deve estar entre 0 e 100.")
        return None

    return luminosity


def read_aggregate_operation():
    print("\nOperacoes:")
    print("1. Media")
    print("2. Desvio padrao")
    print("3. Minimo")
    print("4. Maximo")

    option = input("Escolha uma operacao: ").strip()

    if option == "1":
        return client_pb2.AGGREGATE_OPERATION_AVG
    if option == "2":
        return client_pb2.AGGREGATE_OPERATION_STDDEV
    if option == "3":
        return client_pb2.AGGREGATE_OPERATION_MIN
    if option == "4":
        return client_pb2.AGGREGATE_OPERATION_MAX

    print("Operacao invalida.")
    return None


def read_window_seconds():
    value = input("Janela em segundos (0 para todas as leituras): ").strip()
    if value == "":
        return 0

    try:
        window_seconds = int(value)
    except ValueError:
        print("Janela invalida.")
        return None

    if window_seconds < 0:
        print("A janela nao pode ser negativa.")
        return None

    return window_seconds


def aggregate_operation_name(operation):
    names = {
        client_pb2.AGGREGATE_OPERATION_AVG: "AVG",
        client_pb2.AGGREGATE_OPERATION_STDDEV: "STDDEV",
        client_pb2.AGGREGATE_OPERATION_MIN: "MIN",
        client_pb2.AGGREGATE_OPERATION_MAX: "MAX",
    }

    return names.get(operation, "UNKNOWN")


def main_menu():
    while True:
        print("\n=== Cliente Analitico ===")
        print("1. Listar fontes de dados")
        print("2. Listar todas as leituras")
        print("3. Ajustar fonte controlavel")
        print("4. Simular falha em fonte controlavel")
        print("5. Consulta")
        print("0. Sair")

        option = input("Escolha uma opcao: ").strip()

        if option == "1":
            list_sources()
        elif option == "2":
            list_readings()
        elif option == "3":
            adjust_controllable_source()
        elif option == "4":
            simulate_failure()
        elif option == "5":
            aggregate_query()
        elif option == "0":
            print("Cliente encerrado.")
            return
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main_menu()
