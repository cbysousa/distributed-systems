package discovery

import (
	"fmt"
	"net"
	"strconv"
	"time"

	smartpb "github.com/cbysousa/distributed-systems/internal/proto"
	"google.golang.org/protobuf/proto"
)

type Source struct {
	Name         string
	Type         string
	Address      string
	IP           string
	Port         int
	Controllable bool
	Status       string
}

func Discover(cfg Config) ([]Source, error) {
	multicastAddr, err := net.ResolveUDPAddr("udp4", fmt.Sprintf("%s:%d", cfg.MulticastAddress, cfg.DiscoveryPort))
	if err != nil {
		return nil, err
	}

	conn, err := net.ListenUDP("udp4", &net.UDPAddr{
		IP:   net.IPv4zero,
		Port: 0,
	})
	if err != nil {
		return nil, err
	}
	defer conn.Close()

	request := &smartpb.DiscoveryRequest{
		GatewayId:    cfg.GatewayID,
		GatewayIp:    cfg.GatewayIP,
		ReadingsPort: int32(cfg.ReadingsPort),
		ClientPort:   int32(cfg.ClientPort),
	}

	data, err := proto.Marshal(request)
	if err != nil {
		return nil, err
	}

	_, err = conn.WriteToUDP(data, multicastAddr)
	if err != nil {
		return nil, err
	}

	foundSources := make(chan Source, 16)
	done := make(chan struct{})

	go listenForResponses(conn, cfg.BufferSize, foundSources, done)

	sources := make([]Source, 0)
	seenSources := make(map[string]bool)
	timeout := time.After(time.Duration(cfg.TimeoutSeconds) * time.Second)

	for {
		select {
		case source := <-foundSources:
			if seenSources[source.Name] {
				continue
			}

			seenSources[source.Name] = true
			sources = append(sources, source)
		case <-timeout:
			close(done)
			return sources, nil
		}
	}
}

func listenForResponses(conn *net.UDPConn, bufferSize int, foundSources chan<- Source, done <-chan struct{}) {
	buffer := make([]byte, bufferSize)

	for {
		n, remoteAddr, err := conn.ReadFromUDP(buffer)
		if err != nil {
			return
		}

		source, err := parseSourceResponse(buffer[:n], remoteAddr)
		if err != nil {
			continue
		}

		select {
		case foundSources <- source:
		case <-done:
			return
		}
	}
}

func parseSourceResponse(data []byte, remoteAddr *net.UDPAddr) (Source, error) {
	response := &smartpb.DiscoveryResponse{}
	if err := proto.Unmarshal(data, response); err != nil {
		return Source{}, err
	}

	if response.SourceName == "" {
		return Source{}, fmt.Errorf("discovery response missing source name")
	}

	ip := response.Ip
	if ip == "" {
		ip = remoteAddr.IP.String()
	}

	port := int(response.ControlPort)
	address := ""
	if port > 0 {
		address = net.JoinHostPort(ip, strconv.Itoa(port))
	}

	return Source{
		Name:         response.SourceName,
		Type:         response.SourceType,
		Address:      address,
		IP:           ip,
		Port:         port,
		Controllable: response.Controllable,
		Status:       response.Status,
	}, nil
}
