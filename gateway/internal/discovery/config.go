package discovery

type Config struct {
	MulticastAddress string
	DiscoveryPort    int
	TimeoutSeconds   int
	BufferSize       int
	GatewayID        string
	GatewayIP        string
	ReadingsPort     int
	ClientPort       int
}

func DefaultConfig() Config {
	return Config{
		MulticastAddress: "239.0.0.1",
		DiscoveryPort:    9999,
		TimeoutSeconds:   3,
		BufferSize:       1024,
		GatewayID:        "gateway-1",
		GatewayIP:        "",
		ReadingsPort:     11000,
		ClientPort:       12000,
	}
}
