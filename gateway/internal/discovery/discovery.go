package discovery

import (
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"
)

const discoveryMessage = "DISCOVER"

type Source struct {
	Name         string
	Address      string
	IP           string
	Port         int
	Controllable bool
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

	_, err = conn.WriteToUDP([]byte(discoveryMessage), multicastAddr)
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
			key := source.Name + "@" + source.Address
			if seenSources[key] {
				continue
			}

			seenSources[key] = true
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

		source, err := parseSourceResponse(string(buffer[:n]), remoteAddr)
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

func parseSourceResponse(response string, remoteAddr *net.UDPAddr) (Source, error) {
	parts := strings.Split(strings.TrimSpace(response), "|")
	if len(parts) != 3 {
		return Source{}, fmt.Errorf("invalid discovery response: %s", response)
	}

	port, err := strconv.Atoi(parts[2])
	if err != nil {
		return Source{}, err
	}

	ip := remoteAddr.IP.String()

	return Source{
		Name:         parts[0],
		Address:      net.JoinHostPort(ip, strconv.Itoa(port)),
		IP:           ip,
		Port:         port,
		Controllable: parts[1] == "1",
	}, nil
}
