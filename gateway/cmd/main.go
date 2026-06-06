package main

import (
	"log"
	"time"

	"github.com/cbysousa/distributed-systems/internal/clientserver"
	"github.com/cbysousa/distributed-systems/internal/discovery"
	"github.com/cbysousa/distributed-systems/internal/readings"
	"github.com/cbysousa/distributed-systems/internal/state"
)

const discoveryInterval = 5 * time.Second

func main() {
	gatewayState := state.NewGatewayState()
	discoveryConfig := discovery.DefaultConfig()

	go startPeriodicDiscovery(gatewayState, discoveryConfig)

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

func startPeriodicDiscovery(gatewayState *state.GatewayState, cfg discovery.Config) {
	discoverSources(gatewayState, cfg)
	for {
		time.Sleep(discoveryInterval)
		discoverSources(gatewayState, cfg)
	}
}

func discoverSources(gatewayState *state.GatewayState, cfg discovery.Config) {
	sources, err := discovery.Discover(cfg)
	if err != nil {
		log.Println(err)
		return
	}

	gatewayState.AddDiscoveredSources(sources)
	for _, source := range sources {
		log.Printf("source discovered: name=%s type=%s address=%s controllable=%t status=%s", source.Name, source.Type, source.Address, source.Controllable, source.Status)
	}
}
