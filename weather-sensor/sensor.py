import socket
import struct
import time
import threading
import random
import temperature_pb2

MULTICAST_GROUP = "239.0.0.1"
DISCOVERY_PORT = 9999
NAME = "temperature_sensor"
CONTROLLABLE = "0"  #sensor contínuo (não recebe comandos tcp)
DATA_PORT = 8081    #porta udp dedicada no gateway pra receber leituras contínuas

gateway_ip = None

def listen_multicast():
    #thread que escuta o broadcast do gateway para se apresentar
    global gateway_ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", DISCOVERY_PORT))
    
    membership = struct.pack("4s4s", socket.inet_aton(MULTICAST_GROUP), socket.inet_aton("0.0.0.0"))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    
    print(f"[{NAME}] Aguardando o Gateway no multicast...")
    
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode("utf-8").strip()
        
        if message == "DISCOVER":
            gateway_ip = addr[0]
            
            response = f"{NAME}|{CONTROLLABLE}|0"
            sock.sendto(response.encode("utf-8"), addr)
            print(f"[{NAME}] Conectado ao Gateway em {gateway_ip}")

def send_continuous_data():
    #loop principal que gera e envia os dados via protobuf e udp
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while True:
        if gateway_ip:
            #simula a leitura de um sensor entre 20°C e 35°C
            current_temp = round(random.uniform(20.0, 35.0), 1)
            
            reading = temperature_pb2.TemperatureReading()
            reading.value = current_temp
            reading.unit = "C"
            
            try:
                #serializa pra binário e envia via udp
                sock.sendto(reading.SerializeToString(), (gateway_ip, DATA_PORT))
                print(f"[{NAME}] Enviado: {current_temp}°C")
            except Exception as e:
                print(f"[{NAME}] Erro ao enviar: {e}")
                
        #frequência de envio das leituras contínuas
        time.sleep(5)

if __name__ == "__main__":
    discovery_thread = threading.Thread(target=listen_multicast, daemon=True)
    discovery_thread.start()
    
    send_continuous_data()