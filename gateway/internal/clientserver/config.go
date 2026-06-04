package clientserver

type Config struct {
	ListenAddress string
	ListenPort    int
}

func DefaultConfig() Config {
	return Config{
		ListenAddress: "0.0.0.0",
		ListenPort:    12000,
	}
}
