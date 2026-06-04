package main

import (
	"fmt"
	"log"

	"github.com/cbysousa/distributed-systems/internal/clientserver"
	"github.com/cbysousa/distributed-systems/internal/discovery"
	"github.com/cbysousa/distributed-systems/internal/readings"
	"github.com/cbysousa/distributed-systems/internal/state"
)

func main() {
	sources, err := discovery.Discover(discovery.DefaultConfig())
	if err != nil {
		log.Fatal(err)
	}

	gatewayState := state.NewGatewayState()
	gatewayState.AddDiscoveredSources(sources)

	for _, source := range gatewayState.ListSources() {
		fmt.Println(source.Address, source.Name, source.Controllable, source.Status)
	}

	go func() {
		if err := readings.StartUDPServer(readings.DefaultConfig(), gatewayState); err != nil {
			log.Println(err)
		}
	}()

	go func() {
		if err := clientserver.StartTCPServer(clientserver.DefaultConfig(), gatewayState); err != nil {
			log.Println(err)
		}
	}()

	select {}
}
