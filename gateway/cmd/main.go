package main

import (
	"log"
	"time"

	"github.com/cbysousa/distributed-systems/internal/clientserver"
	"github.com/cbysousa/distributed-systems/internal/discovery"
	"github.com/cbysousa/distributed-systems/internal/history"
	"github.com/cbysousa/distributed-systems/internal/readings"
	"github.com/cbysousa/distributed-systems/internal/state"
)

const discoveryInterval = 5 * time.Second

func main() {
	gatewayState := state.NewGatewayState()
	historyStore := startHistoryStore(gatewayState)
	discoveryConfig := discovery.DefaultConfig()

	go startPeriodicDiscovery(gatewayState, discoveryConfig)

	go func() {
		if err := readings.StartUDPServer(
			readings.DefaultConfig(),
			gatewayState,
			historyStore,
		); err != nil {
			log.Println(err)
		}
	}()

	go func() {
		if err := clientserver.StartTCPServer(
			clientserver.DefaultConfig(),
			gatewayState,
		); err != nil {
			log.Println(err)
		}
	}()

	select {}
}

func startHistoryStore(gatewayState *state.GatewayState) *history.CSVStore {
	historyStore, err := history.NewCSVStore(history.DefaultCSVPath())
	if err != nil {
		log.Printf("history persistence disabled: %v", err)
		return nil
	}

	readings, err := historyStore.LoadReadings()
	if err != nil {
		log.Printf("failed to load reading history: %v", err)
		return historyStore
	}

	gatewayState.AddReadings(readings)
	log.Printf("loaded %d historical readings", len(readings))

	return historyStore
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
		log.Printf(
			"source discovered: name=%s type=%s address=%s controllable=%t status=%s",
			source.Name,
			source.Type,
			source.Address,
			source.Controllable,
			source.Status,
		)
	}
}