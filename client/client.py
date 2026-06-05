import socket


GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 8080


def receive(sock):
    data = sock.recv(4096)
    if not data:
        return None
    return data.decode("utf-8")


def send_command(sock, command):
    sock.sendall((command + "\n").encode("utf-8"))
    return receive(sock)


def main():
    print("Cliente Analítico - Cidade Inteligente")
    print(f"Conectando ao Gateway em {GATEWAY_HOST}:{GATEWAY_PORT}...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((GATEWAY_HOST, GATEWAY_PORT))
    except ConnectionRefusedError:
        print("Erro: Gateway indisponível.")
        print("Verifique se o container do Gateway está em execução.")
        return

    try:
        msg = receive(sock)
        if msg:
            print(msg, end="")

        msg = receive(sock)
        if msg:
            print(msg, end="")

        while True:
            print("\nMenu:")
            print("1 - Listar fontes descobertas")
            print("2 - Ajuda")
            print("0 - Sair")

            option = input("Escolha uma opção: ").strip()

            if option == "1":
                command = "LIST"
            elif option == "2":
                command = "HELP"
            elif option == "0":
                response = send_command(sock, "EXIT")
                if response:
                    print(response, end="")
                break
            else:
                print("Opção inválida.")
                continue

            response = send_command(sock, command)

            if response is None:
                print("Conexão encerrada pelo Gateway.")
                break

            print("\nResposta do Gateway:")
            print(response, end="")

    finally:
        sock.close()
        print("Cliente encerrado.")


if __name__ == "__main__":
    main()