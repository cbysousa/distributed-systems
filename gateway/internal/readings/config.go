package readings

type Config struct {
	ListenAddress string
	ListenPort    int
	BufferSize    int
}

func DefaultConfig() Config {
	return Config{
		ListenAddress: "0.0.0.0",
		ListenPort:    11000,
		BufferSize:    4096,
	}
}
