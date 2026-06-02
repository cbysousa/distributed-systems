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



if __name__ == "__main__":
    main()