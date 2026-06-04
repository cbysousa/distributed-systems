package clientserver

import (
	"io"
	"log"
	"net"
	"strconv"

	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/state"
	"github.com/cbysousa/distributed-systems/internal/tcpmessage"
	"google.golang.org/protobuf/proto"
)

func StartTCPServer(cfg Config, gatewayState *state.GatewayState) error {
	addr := net.JoinHostPort(cfg.ListenAddress, strconv.Itoa(cfg.ListenPort))
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	defer listener.Close()

	log.Printf("client TCP server listening on %s\n", addr)

	for {
		conn, err := listener.Accept()
		if err != nil {
			return err
		}

		go handleConnection(conn, gatewayState)
	}
}

func handleConnection(conn net.Conn, gatewayState *state.GatewayState) {
	defer conn.Close()

	for {
		data, err := tcpmessage.Read(conn)
		if err != nil {
			if err != io.EOF {
				log.Println(err)
			}
			return
		}

		request := &smartpb.ClientRequest{}
		if err := proto.Unmarshal(data, request); err != nil {
			writeResponse(conn, errorResponse("invalid protobuf request"))
			continue
		}

		response := handleRequest(request, gatewayState)
		writeResponse(conn, response)
	}
}

func writeResponse(conn net.Conn, response *smartpb.ClientResponse) {
	data, err := proto.Marshal(response)
	if err != nil {
		log.Println(err)
		return
	}

	if err := tcpmessage.Write(conn, data); err != nil {
		log.Println(err)
	}
}
