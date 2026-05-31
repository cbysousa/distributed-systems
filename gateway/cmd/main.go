package main

import (
	"fmt"
	"log"
	"net"
	"strings"
)

type DataSource struct {
	Controllable bool
	Address      string
	Name         string
}

var sources []DataSource

func init() {
	sources = make([]DataSource, 0, 5)
	addr, err := net.ResolveUDPAddr("udp4", "239.0.0.1:9999")
	if err != nil {
		panic(err)
	}
	conn, err := net.ListenUDP("udp4", &net.UDPAddr{
		IP:   net.IPv4zero,
		Port: 0,
	})
	if err != nil {
		panic(err)
	}

	defer conn.Close()

	msg := "DISCOVER"
	_, err = conn.WriteToUDP([]byte(msg), addr)
	if err != nil {
		panic(err)
	}
	buf := make([]byte, 1024)
	for {
		n, rAddr, err := conn.ReadFromUDP(buf)
		if err != nil {
			break
		}
		parts := strings.Split(string(buf[:n]), "|")
		if len(parts) < 3 {
			continue
		}
		src := DataSource{
			Controllable: parts[1] == "1",
			Address:      net.JoinHostPort(rAddr.IP.String(), parts[2]),
			Name:         parts[0],
		}
		sources = append(sources, src)
		log.Println(len(sources))
		if len(sources) == 3 {
			break
		}
	}
}

func main() {
	for _, s := range sources {
		fmt.Println(s.Address, s.Name)
	}
}
