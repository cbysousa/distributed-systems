package state

import (
	"strings"
	"sync"
	"time"

	"github.com/cbysousa/distributed-systems/internal/discovery"
)

const (
	StatusActive  = "ACTIVE"
	StatusOffline = "OFFLINE"
)

func NormalizeStatus(status string) string {
	if strings.ToUpper(status) == StatusOffline {
		return StatusOffline
	}

	return StatusActive
}

type Source struct {
	Name         string
	Type         string
	Address      string
	IP           string
	Port         int
	Controllable bool
	Status       string
	LastSeen     time.Time
}

type Reading struct {
	SourceName string
	SourceType string
	Metric     string
	Value      float64
	Unit       string
	Timestamp  time.Time
}

type GatewayState struct {
	mutex    sync.RWMutex
	sources  map[string]Source
	readings []Reading
}

func NewGatewayState() *GatewayState {
	return &GatewayState{
		sources:  make(map[string]Source),
		readings: make([]Reading, 0),
	}
}

func (s *GatewayState) AddDiscoveredSources(sources []discovery.Source) {
	for _, source := range sources {
		s.AddDiscoveredSource(source)
	}
}

func (s *GatewayState) AddDiscoveredSource(source discovery.Source) {
	s.AddSource(Source{
		Name:         source.Name,
		Type:         source.Type,
		Address:      source.Address,
		IP:           source.IP,
		Port:         source.Port,
		Controllable: source.Controllable,
		Status:       source.Status,
		LastSeen:     time.Now(),
	})
}

func (s *GatewayState) AddSource(source Source) {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	source.Status = NormalizeStatus(source.Status)

	if source.LastSeen.IsZero() {
		source.LastSeen = time.Now()
	}

	s.sources[source.Name] = source
}

func (s *GatewayState) ListSources() []Source {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	sources := make([]Source, 0, len(s.sources))
	for _, source := range s.sources {
		sources = append(sources, source)
	}

	return sources
}

func (s *GatewayState) GetSource(name string) (Source, bool) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	source, exists := s.sources[name]
	return source, exists
}

func (s *GatewayState) UpdateStatus(name string, status string) bool {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	source, exists := s.sources[name]
	if !exists {
		return false
	}

	source.Status = NormalizeStatus(status)
	s.sources[name] = source
	return true
}

func (s *GatewayState) UpdateLastSeen(name string) bool {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	source, exists := s.sources[name]
	if !exists {
		return false
	}

	source.LastSeen = time.Now()
	s.sources[name] = source
	return true
}

func (s *GatewayState) AddReading(reading Reading) {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if reading.Timestamp.IsZero() {
		reading.Timestamp = time.Now()
	}

	s.readings = append(s.readings, reading)
}

func (s *GatewayState) AddReadings(readings []Reading) {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	now := time.Now()
	for _, reading := range readings {
		if reading.Timestamp.IsZero() {
			reading.Timestamp = now
		}

		s.readings = append(s.readings, reading)
	}
}

func (s *GatewayState) ListReadings() []Reading {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	readings := make([]Reading, len(s.readings))
	copy(readings, s.readings)

	return readings
}

func (s *GatewayState) ListReadingsByMetric(metric string) []Reading {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	readings := make([]Reading, 0)
	for _, reading := range s.readings {
		if reading.Metric == metric {
			readings = append(readings, reading)
		}
	}

	return readings
}
