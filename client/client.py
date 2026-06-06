import socket
import struct

import client_pb2


GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 12000


def read_exact(sock, size):
    data = b""

    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk

    return data


def send_proto(sock, message):
    data = message.SerializeToString()
    header = struct.pack(">I", len(data))
    sock.sendall(header + data)


def receive_proto(sock):
    header = read_exact(sock, 4)
    if header is None:
        return None

    size = struct.unpack(">I", header)[0]

    data = read_exact(sock, size)
    if data is None:
        return None

    response = client_pb2.ClientResponse()
    response.ParseFromString(data)
    return response


def request_list_sources(sock):
    request = client_pb2.ClientRequest(
        list_sources=client_pb2.ListSourcesRequest()
    )

    send_proto(sock, request)
    response = receive_proto(sock)

    if response is None:
        print("Gateway encerrou a conexão.")
        return

    print(f"\nStatus: {response.success}")
    print(f"Mensagem: {response.message}")

    if not response.HasField("list_sources"):
        return

    sources = response.list_sources.sources

    if not sources:
        print("Nenhuma fonte descoberta.")
        return

    print("\nFontes descobertas:")
    for index, source in enumerate(sources, start=1):
        print(
            f"{index}. {source.name} | "
            f"tipo={source.source_type} | "
            f"endereço={source.address} | "
            f"controlável={source.controllable} | "
            f"status={source.status}"
        )


def request_list_readings(sock):
    metric = input("Filtrar por métrica, ou ENTER para todas: ").strip()

    request = client_pb2.ClientRequest(
        list_readings=client_pb2.ListReadingsRequest(metric=metric)
    )

    send_proto(sock, request)
    response = receive_proto(sock)

    if response is None:
        print("Gateway encerrou a conexão.")
        return

    print(f"\nStatus: {response.success}")
    print(f"Mensagem: {response.message}")

    if not response.HasField("list_readings"):
        return

    readings = response.list_readings.readings

    if not readings:
        print("Nenhuma leitura registrada.")
        return

    print("\nLeituras:")
    for index, reading in enumerate(readings, start=1):
        print(
            f"{index}. fonte={reading.source_name} | "
            f"tipo={reading.source_type} | "
            f"métrica={reading.metric} | "
            f"valor={reading.value} {reading.unit} | "
            f"timestamp={reading.timestamp_unix_ms}"
        )


def main():
    print("Cliente Analítico - Cidade Inteligente")
    print(f"Conectando ao Gateway em {GATEWAY_HOST}:{GATEWAY_PORT}...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((GATEWAY_HOST, GATEWAY_PORT))
    except ConnectionRefusedError:
        print("Erro: não foi possível conectar ao Gateway.")
        print("Verifique se o Gateway está rodando na porta 12000.")
        return

    try:
        while True:
            print("\nMenu:")
            print("1 - Listar fontes descobertas")
            print("2 - Listar leituras recebidas")
            print("0 - Sair")

            option = input("Escolha uma opção: ").strip()

            if option == "1":
                request_list_sources(sock)

            elif option == "2":
                request_list_readings(sock)

            elif option == "0":
                break

            else:
                print("Opção inválida.")

    finally:
        sock.close()
        print("Cliente encerrado.")


if __name__ == "__main__":
    main()