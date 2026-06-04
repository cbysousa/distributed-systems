package readings

import (
	"fmt"
	"net"
	"strconv"

	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"github.com/cbysousa/distributed-systems/internal/state"
	"google.golang.org/protobuf/proto"
)

func StartUDPServer(cfg Config, gatewayState *state.GatewayState) error {
	addr, err := net.ResolveUDPAddr("udp4", net.JoinHostPort(cfg.ListenAddress, strconv.Itoa(cfg.ListenPort)))
	if err != nil {
		return err
	}

	conn, err := net.ListenUDP("udp4", addr)
	if err != nil {
		return err
	}
	defer conn.Close()

	buffer := make([]byte, cfg.BufferSize)

	for {
		n, _, err := conn.ReadFromUDP(buffer)
		if err != nil {
			return err
		}

		packet := &smartpb.ReadingPacket{}
		if err := proto.Unmarshal(buffer[:n], packet); err != nil {
			continue
		}

		readings := packetToReadings(packet)
		if len(readings) == 0 {
			continue
		}

		gatewayState.AddReadings(readings)
		gatewayState.UpdateLastSeen(packet.SourceName)

		fmt.Printf("received %d readings from %s\n", len(readings), packet.SourceName)
	}
}
